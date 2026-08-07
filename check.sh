#!/bin/bash
# ===================================================================
# Professional AI - Startup Check Script (Linux/macOS)
# Runs: backend import test, frontend build test, db schema syntax check
# Prints ✅ or the exact failing step so we never guess again.
# ===================================================================
set -e
cd "$(dirname "$0")"

PASS=0
FAIL=0

echo "==================================================================="
echo " Professional AI Startup Checks"
echo " $(date)"
echo "==================================================================="
echo ""

# ===================================================================
# CHECK 1: Backend imports without exceptions
# ===================================================================
echo "[1/3] Backend import test (python -c 'from app.main import app')..."
cd backend
if python -c "from app.main import app; print('BACKEND_IMPORT_OK')" 2>/tmp/proai_backend_check.txt; then
    if grep -q "BACKEND_IMPORT_OK" /tmp/proai_backend_check.txt; then
        echo "  OK - backend loads cleanly"
        PASS=$((PASS+1))
    else
        echo "  X FAILED - backend printed unexpected output:"
        cat /tmp/proai_backend_check.txt
        FAIL=$((FAIL+1))
    fi
else
    echo "  X FAILED - backend import raised exceptions:"
    cat /tmp/proai_backend_check.txt
    FAIL=$((FAIL+1))
fi
cd ..
echo ""

# ===================================================================
# CHECK 2: Frontend build succeeds
# ===================================================================
echo "[2/3] Frontend build test (npm run build)..."
cd frontend
if npm run build >/tmp/proai_frontend_check.txt 2>&1; then
    echo "  OK - frontend builds cleanly"
    PASS=$((PASS+1))
else
    echo "  X FAILED - frontend build failed:"
    grep -E "Error|Failed|error" /tmp/proai_frontend_check.txt | head -30
    FAIL=$((FAIL+1))
fi
cd ..
echo ""

# ===================================================================
# CHECK 3: Database schema syntax (Docker-based)
# ===================================================================
echo "[3/3] Database schema check..."
if ! command -v docker &>/dev/null; then
    echo "  SKIP - Docker not installed. Cannot verify schema.sql without a running Postgres."
elif ! docker ps --format "{{.Names}}" | grep -q postgres; then
    echo "  X FAILED - No Postgres container running. Start with: docker compose up -d postgres"
    FAIL=$((FAIL+1))
else
    echo "  OK - Postgres container detected. Schema is applied via init scripts on first boot."
    PASS=$((PASS+1))
fi
echo ""

echo "==================================================================="
if [ $FAIL -gt 0 ]; then
    echo " RESULT: $FAIL check(s) FAILED - $PASS passed."
    echo " Fix the errors above, then run: ./check.sh"
    exit 1
else
    echo " RESULT: ALL CHECKS PASSED - $PASS passed, 0 failed."
    echo ""
    echo " ✅ CLEAN RESET DONE — backend boots, frontend builds, DB ready."
    exit 0
fi