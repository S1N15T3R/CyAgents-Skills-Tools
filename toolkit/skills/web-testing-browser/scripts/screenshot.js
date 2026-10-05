#!/usr/bin/env node
/** screenshot.js — capture a PNG (full page, or an element via --selector). Authorized testing only. */
'use strict';
const path = require('path');
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  const outPath = args.out || path.join(process.cwd(), `screenshot-${Date.now()}.png`);
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });
    if (args.selector) {
      const el = await page.$(args.selector);
      if (!el) throw new Error(`Selector not found: ${args.selector}`);
      await el.screenshot({ path: outPath });
    } else {
      await page.screenshot({ path: outPath, fullPage: args.fullPage !== false });
    }
    outputJSON({ url: page.url(), path: outPath, selector: args.selector || null });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
