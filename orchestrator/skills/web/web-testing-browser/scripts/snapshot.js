#!/usr/bin/env node
/**
 * snapshot.js — enumerate interactive elements (links, buttons, inputs, forms) with selectors and XPath.
 * The attack-surface / form-discovery primitive. Authorized testing only.
 */
'use strict';
const { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } = require('./lib/browser');

(async () => {
  const args = parseArgs();
  if (!args.url) return outputError('Missing --url');
  let browser;
  try {
    browser = await getBrowser({ headless: args.headless });
    const page = await getPage(browser);
    await page.goto(args.url, { waitUntil: args['wait-until'], timeout: Number(args.timeout) });

    const data = await page.evaluate(() => {
      const cssPath = (el) => {
        if (el.id) return `#${el.id}`;
        const parts = [];
        while (el && el.nodeType === 1 && parts.length < 5) {
          let sel = el.nodeName.toLowerCase();
          if (el.className && typeof el.className === 'string') {
            const c = el.className.trim().split(/\s+/).slice(0, 2).join('.');
            if (c) sel += '.' + c;
          }
          const parent = el.parentNode;
          if (parent) {
            const sibs = Array.from(parent.children).filter(n => n.nodeName === el.nodeName);
            if (sibs.length > 1) sel += `:nth-of-type(${sibs.indexOf(el) + 1})`;
          }
          parts.unshift(sel);
          el = el.parentNode;
        }
        return parts.join(' > ');
      };
      const info = (el) => ({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type') || null,
        id: el.id || null,
        name: el.getAttribute('name') || null,
        placeholder: el.getAttribute('placeholder') || null,
        href: el.getAttribute('href') || null,
        action: el.getAttribute('action') || null,
        method: el.getAttribute('method') || null,
        text: (el.innerText || el.value || '').trim().slice(0, 80) || null,
        selector: cssPath(el),
      });
      const sel = 'a[href], button, input, textarea, select, form, [onclick], [role=button], [contenteditable]';
      const els = Array.from(document.querySelectorAll(sel));
      const forms = els.filter(e => e.tagName === 'FORM').map(info);
      const inputs = els.filter(e => ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.tagName)).map(info);
      const links = els.filter(e => e.tagName === 'A').map(info);
      const buttons = els.filter(e => e.tagName === 'BUTTON' || e.getAttribute('role') === 'button').map(info);
      return { counts: { forms: forms.length, inputs: inputs.length, links: links.length, buttons: buttons.length }, forms, inputs, links, buttons };
    });

    outputJSON({ url: page.url(), ...data });
  } catch (e) {
    outputError(e);
  } finally {
    await closeBrowser(browser, args.close === false || args.close === 'false');
  }
})();
