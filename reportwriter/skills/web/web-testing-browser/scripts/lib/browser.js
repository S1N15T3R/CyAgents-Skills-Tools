/**
 * lib/browser.js — shared Puppeteer helpers for the web-testing-browser skill.
 *
 * Adapted from the Apache-2.0 "chrome-devtools" skill (mrgoonie/claudekit-skills).
 * One action per script; JSON to stdout; errors to stderr as {success:false,error}.
 *
 * For authorized security testing only.
 */
'use strict';

const fs = require('fs');
const path = require('path');

let puppeteer;
try {
  puppeteer = require('puppeteer');
} catch (e) {
  // Defer the failure to runtime so scripts emit a clean JSON error instead of a stack trace.
  puppeteer = null;
}

const ENDPOINT_FILE = path.join(__dirname, '..', '.browser-endpoint');

const DEFAULT_LAUNCH_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage',
];

/**
 * Get a browser. If a persistent endpoint file exists, connect to that shared
 * (logged-in) browser; otherwise launch a fresh one.
 *
 * options: { headless=true, connect=true, args=[], defaultViewport }
 */
async function getBrowser(options = {}) {
  if (!puppeteer) {
    throw new Error(
      "puppeteer is not installed. Run 'npm install' in the skill's scripts/ directory."
    );
  }

  const {
    headless = true,
    connect = true,
    args = [],
    defaultViewport = { width: 1920, height: 1080 },
  } = options;

  // Reuse a persistent authenticated session if one is running.
  if (connect && fs.existsSync(ENDPOINT_FILE)) {
    try {
      const wsEndpoint = fs.readFileSync(ENDPOINT_FILE, 'utf8').trim();
      if (wsEndpoint) {
        const browser = await puppeteer.connect({
          browserWSEndpoint: wsEndpoint,
          defaultViewport,
        });
        browser.__persistent = true;
        return browser;
      }
    } catch (e) {
      // Stale endpoint — fall through to a fresh launch.
    }
  }

  // --- Optional stealth ---------------------------------------------------
  // For bot-protected targets, prefer the stealth-browser-mcp (see mcp/).
  // To add evasion here instead: `npm i puppeteer-extra puppeteer-extra-plugin-stealth`,
  // then require('puppeteer-extra').use(require('puppeteer-extra-plugin-stealth')())
  // and launch from that instead of `puppeteer`.
  // -----------------------------------------------------------------------

  const browser = await puppeteer.launch({
    headless: headless === true || headless === 'true' ? 'new' : false,
    args: [...DEFAULT_LAUNCH_ARGS, ...args],
    defaultViewport,
  });
  browser.__persistent = false;
  return browser;
}

async function getPage(browser) {
  const pages = await browser.pages();
  return pages.length ? pages[0] : await browser.newPage();
}

/**
 * Close a browser unless it's the shared persistent one, or unless --close false
 * was passed (keepOpen=true) to allow chaining commands against the same browser.
 */
async function closeBrowser(browser, keepOpen = false) {
  if (!browser) return;
  if (browser.__persistent) {
    // Detach from the shared session without killing it.
    try { await browser.disconnect(); } catch (e) { /* ignore */ }
    return;
  }
  if (keepOpen) return;
  try { await browser.close(); } catch (e) { /* ignore */ }
}

/** Parse argv with yargs if available, else a tiny --k v / --flag parser. */
function parseArgs() {
  try {
    const yargs = require('yargs/yargs');
    const { hideBin } = require('yargs/helpers');
    return yargs(hideBin(process.argv))
      .option('url', { type: 'string', describe: 'Target URL' })
      .option('headless', { default: true })
      .option('close', { type: 'boolean', default: true, describe: 'Close browser after run' })
      .option('timeout', { type: 'number', default: 30000 })
      .option('wait-until', { type: 'string', default: 'networkidle2' })
      .help(false).version(false)
      .parseSync();
  } catch (e) {
    const out = { headless: true, close: true, timeout: 30000, 'wait-until': 'networkidle2' };
    const a = process.argv.slice(2);
    for (let i = 0; i < a.length; i++) {
      if (a[i].startsWith('--')) {
        const key = a[i].slice(2);
        const next = a[i + 1];
        if (next === undefined || next.startsWith('--')) { out[key] = true; }
        else { out[key] = next; i++; }
      }
    }
    return out;
  }
}

function outputJSON(data) {
  process.stdout.write(JSON.stringify({ success: true, ...data }, null, 2) + '\n');
}

function outputError(error) {
  const msg = error && error.message ? error.message : String(error);
  process.stderr.write(JSON.stringify({ success: false, error: msg }, null, 2) + '\n');
  process.exitCode = 1;
}

module.exports = {
  getBrowser,
  getPage,
  closeBrowser,
  parseArgs,
  outputJSON,
  outputError,
  ENDPOINT_FILE,
};
