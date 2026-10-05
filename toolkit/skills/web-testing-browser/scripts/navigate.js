#!/usr/bin/env node
/** navigate.js — load a URL; return final URL, HTTP status, and title. Authorized testing only. */
'use strict';
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    const resp = await page.goto(args.url, {
      waitUntil: args['wait-until'],
      timeout: Number(args.timeout),
    });
    outputJSON({
      url: page.url(),
      requestedUrl: args.url,
      status: resp ? resp.status() : null,
      title: await page.title(),
    });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
