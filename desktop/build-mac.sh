#!/bin/bash
set -e

echo "========================================"
echo "Professional AI Desktop - macOS Build"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "[1/3] Installing dependencies..."
npm install

echo ""
echo "[2/3] Building macOS DMG..."
npm run dist -- --mac

echo ""
echo "[3/3] Done!"
echo ""
echo "Installer location: desktop/release/Professional AI.dmg"
echo ""
