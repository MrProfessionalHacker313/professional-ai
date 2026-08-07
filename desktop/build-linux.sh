#!/bin/bash
set -e

echo "========================================"
echo "Professional AI Desktop - Linux Build"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "[1/3] Installing dependencies..."
npm install

echo ""
echo "[2/3] Building Linux AppImage..."
npm run dist -- --linux

echo ""
echo "[3/3] Done!"
echo ""
echo "Installer location: desktop/release/Professional AI.AppImage"
echo ""
