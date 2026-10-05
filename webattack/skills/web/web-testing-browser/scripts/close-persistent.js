#!/usr/bin/env node
/** close-persistent.js — connect to the saved persistent browser, close it, remove .browser-endpoint. */
'use strict';
const fs = require('fs');
const { parseArgs, outputJSON, outputError, ENDPOINT_FILE } = require('./lib/browser');

(async () => {
  parseArgs();
  try {
    if (!fs.existsSync(ENDPOINT_FILE)) return outputJSON({ closed: false, note: 'No persistent session found.' });
    const puppeteer = require('puppeteer');
    const wsEndpoint = fs.readFileSync(ENDPOINT_FILE, 'utf8').trim();
    try {
      const browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
      await browser.close();
    } catch (e) { /* already gone */ }
    fs.unlinkSync(ENDPOINT_FILE);
    outputJSON({ closed: true });
  } catch (e) {
    outputError(e);
  }
})();
