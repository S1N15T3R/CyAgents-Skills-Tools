#!/usr/bin/env node
/** fill.js — type a value into a field. --selector <css> --value <text>. Authorized testing only. */
'use strict';
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  if (!args.selector) return outputError('Missing --selector');
  if (args.value === undefined) return outputError('Missing --value');
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });
    await page.waitForSelector(args.selector, { timeout: Number(args.timeout) });
    if (args.clear !== false) await page.$eval(args.selector, el => { el.value = ''; });
    await page.type(args.selector, String(args.value));
    outputJSON({ url: page.url(), selector: args.selector, filled: true });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
