#!/usr/bin/env node
/** click.js — click an element by selector. --selector <css>. Authorized testing only. */
'use strict';
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  if (!args.selector) return outputError('Missing --selector');
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });
    await page.waitForSelector(args.selector, { timeout: Number(args.timeout) });
    await Promise.all([
      page.click(args.selector),
      page.waitForNavigation({ timeout: Number(args.timeout), waitUntil: args['wait-until'] }).catch(() => {}),
    ]);
    outputJSON({ url: page.url(), selector: args.selector, clicked: true });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
