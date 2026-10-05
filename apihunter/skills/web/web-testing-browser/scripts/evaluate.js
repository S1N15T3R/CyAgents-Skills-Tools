#!/usr/bin/env node
/**
 * evaluate.js — run JavaScript in the page context and return the result.
 * Use for DOM-sink checks, reading document.cookie / storage, probing client state.
 * Pass code via --expr "<js>" or --file <path>. Authorized testing only; benign probes.
 */
'use strict';
const fs = require('fs');
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  let code = args.expr;
  if (!code && args.file) code = fs.readFileSync(args.file, 'utf8');
  if (!code) return outputError('Provide --expr "<js>" or --file <path>');
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });
    // Wrap so both expressions and statement blocks work.
    const result = await page.evaluate((src) => {
      try { return { value: eval(src) }; } // eslint-disable-line no-eval
      catch (err) { return { error: String(err) }; }
    }, code);
    outputJSON({ url: page.url(), result });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
