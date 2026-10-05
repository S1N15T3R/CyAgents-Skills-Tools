#!/usr/bin/env node
/**
 * launch-persistent.js — start a long-lived browser and save its WS endpoint to .browser-endpoint
 * so every other script reuses this (logged-in) session. Launch visible to log in by hand.
 * Authorized testing only.
 *
 *   node launch-persistent.js --headless false --url https://target/login
 *
 * The browser stays open until close-persistent.js is run (or the process is killed).
 */
'use strict';
const fs = require('fs');
const { getBrowser, getPage, parseArgs, outputJSON, outputError, ENDPOINT_FILE } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  try {
    // connect:false so we always launch a NEW browser to own the persistent session.
    const browser = await getBrowser({ headless: args.headless === undefined ? false : args.headless, connect: false });
    const wsEndpoint = browser.wsEndpoint();
    fs.writeFileSync(ENDPOINT_FILE, wsEndpoint);
    if (args.url) {
      const page = await getPage(browser);
      await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) }).catch(() => {});
    }
    outputJSON({
      persistent: true,
      wsEndpoint,
      endpointFile: ENDPOINT_FILE,
      note: 'Log in manually if needed, then run other scripts — they reuse this session. Stop with close-persistent.js.',
    });
    // Detach this process from the browser without closing it.
    browser.disconnect();
    process.exit(0);
  } catch (e) {
    outputError(e);
  }
})();
