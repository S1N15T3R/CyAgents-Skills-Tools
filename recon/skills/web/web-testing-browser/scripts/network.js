#!/usr/bin/env node
/**
 * network.js — record all network requests/responses while loading a URL.
 * Capture APIs, auth headers/tokens, and hidden endpoints. Filter with --types xhr,fetch.
 * Authorized testing only.
 */
'use strict';
const fs = require('fs');
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  const types = args.types ? String(args.types).split(',').map(s => s.trim()) : null;
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    const requests = [];
    const byId = new Map();

    page.on('request', (req) => {
      if (types && !types.includes(req.resourceType())) return;
      const rec = {
        url: req.url(),
        method: req.method(),
        resourceType: req.resourceType(),
        headers: req.headers(),
        postData: req.postData() || null,
        response: null,
      };
      byId.set(req._requestId || req.url() + req.method(), rec);
      requests.push(rec);
    });
    page.on('response', async (resp) => {
      const req = resp.request();
      const rec = byId.get(req._requestId || req.url() + req.method());
      if (rec) {
        rec.response = {
          status: resp.status(),
          statusText: resp.statusText(),
          headers: resp.headers(),
          fromCache: resp.fromCache(),
        };
      }
    });

    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });
    // small settle for late XHRs
    await new Promise(r => setTimeout(r, Number(args.settle || 1500)));

    const result = { url: page.url(), requestCount: requests.length, requests };
    if (args.out) { fs.writeFileSync(args.out, JSON.stringify(result, null, 2)); outputJSON({ url: page.url(), requestCount: requests.length, out: args.out }); }
    else { outputJSON(result); }
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
