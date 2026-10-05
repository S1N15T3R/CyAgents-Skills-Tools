#!/usr/bin/env bash
# install-deps.sh — system libraries Chrome/Puppeteer needs on Linux/WSL.
# On non-Debian systems it just prints guidance. For authorized security testing only.
set -uo pipefail

echo "web-testing-browser: dependency setup"

if ! command -v node >/dev/null 2>&1; then
  echo "  [!] Node.js not found. Install Node 18+ first (e.g. via nvm or your package manager)."
fi

if command -v apt-get >/dev/null 2>&1; then
  echo "  [*] Detected apt. Installing Chrome runtime libraries (may prompt for sudo)..."
  sudo apt-get update -y >/dev/null 2>&1 || true
  sudo apt-get install -y \
    ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libglib2.0-0 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
    lsb-release wget xdg-utils >/dev/null 2>&1 \
    && echo "  [+] System libraries installed." \
    || echo "  [!] Some packages failed — Puppeteer may still work; see its troubleshooting docs."
else
  echo "  [-] Non-apt system. Ensure Chrome/Chromium runtime libs are present, then run: npm install"
fi

echo "  [*] Next: run 'npm install' in this directory to fetch puppeteer + yargs."
