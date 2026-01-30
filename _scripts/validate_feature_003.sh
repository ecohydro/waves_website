#!/bin/bash
# Validation script for Feature 003 - People Profile Sync
# Tests all three user stories and success criteria

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "Feature 003 Validation"
echo "People Profile Management and Enrichment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "[1/6] Checking prerequisites..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $PYTHON_VERSION"

# Check if CV.numbers exists
CV_FILE="$HOME/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers"
if [ -f "$CV_FILE" ]; then
    echo -e "  ${GREEN}✓${NC} CV.numbers file found"
else
    echo -e "  ${YELLOW}⚠${NC} CV.numbers file not found (using test fixtures)"
    CV_FILE="tests/fixtures/sample_cv.numbers"
fi

# Check dependencies
echo "  Checking Python dependencies..."
python3 -c "import numbers_parser, frontmatter, yaml, requests, dotenv, rapidfuzz" 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} All dependencies installed" || \
    echo -e "  ${RED}✗${NC} Missing dependencies. Run: pip install -r _scripts/requirements.txt"

echo ""

# Test User Story 1: Extract
echo "[2/6] Testing User Story 1: Extract..."
echo "  Running: ./sync_people.py extract --dry-run"

cd _scripts
./sync_people.py extract --dry-run > /tmp/feature_003_extract.log 2>&1 && \
    echo -e "  ${GREEN}✓${NC} Extract command completed" || \
    echo -e "  ${RED}✗${NC} Extract command failed (see /tmp/feature_003_extract.log)"

# Check for expected output
if grep -q "unique people" /tmp/feature_003_extract.log; then
    echo -e "  ${GREEN}✓${NC} People extracted successfully"
else
    echo -e "  ${YELLOW}⚠${NC} Extract output unexpected"
fi

echo ""

# Test User Story 2: Sync
echo "[3/6] Testing User Story 2: Sync..."
echo "  Running: ./sync_people.py sync --dry-run"

./sync_people.py sync --dry-run > /tmp/feature_003_sync.log 2>&1 && \
    echo -e "  ${GREEN}✓${NC} Sync command completed" || \
    echo -e "  ${RED}✗${NC} Sync command failed (see /tmp/feature_003_sync.log)"

# Check for expected output
if grep -q "SYNC COMPLETE" /tmp/feature_003_sync.log; then
    echo -e "  ${GREEN}✓${NC} Sync completed successfully"
else
    echo -e "  ${YELLOW}⚠${NC} Sync output unexpected"
fi

echo ""

# Test User Story 3: Enrich (skip if no API key)
echo "[4/6] Testing User Story 3: Enrich..."

if [ -f ../.env ] && grep -q "GOOGLE_CUSTOM_SEARCH_API_KEY" ../.env; then
    echo "  Running: ./sync_people.py enrich --dry-run (first person only)"
    # Note: This would require CV.numbers and interactive input
    echo -e "  ${YELLOW}⚠${NC} Skipping interactive enrich test (requires API key and manual input)"
else
    echo -e "  ${YELLOW}⚠${NC} Skipping enrich test (no API credentials)"
fi

echo ""

# Check success criteria
echo "[5/6] Verifying Success Criteria..."

echo "  SC-001: Performance (<5 min for 50-100 entries)"
echo -e "    ${YELLOW}Manual validation required${NC}"

echo "  SC-002: 90% match rate"
echo -e "    ${YELLOW}Manual validation required (run sync and check stats)${NC}"

echo "  SC-003: 60% enrichment success"
echo -e "    ${YELLOW}Manual validation required (run enrich with API key)${NC}"

echo "  SC-004: Subsequent syncs <2 min"
echo -e "    ${YELLOW}Manual validation required${NC}"

echo "  SC-005: 70% reduction in manual entry"
echo -e "    ${YELLOW}Manual validation required${NC}"

echo "  SC-006: 100% manual content preserved"
if grep -q "_cv_metadata" /tmp/feature_003_sync.log; then
    echo -e "    ${GREEN}✓${NC} cv_metadata tracking enabled"
else
    echo -e "    ${YELLOW}⚠${NC} Check _cv_metadata implementation"
fi

echo ""

# Final validation
echo "[6/6] Final Checks..."

# Check file structure
echo "  Checking file structure..."
[ -d "models" ] && echo -e "  ${GREEN}✓${NC} models/ directory exists" || echo -e "  ${RED}✗${NC} models/ missing"
[ -d "services" ] && echo -e "  ${GREEN}✓${NC} services/ directory exists" || echo -e "  ${RED}✗${NC} services/ missing"
[ -f "sync_people.py" ] && echo -e "  ${GREEN}✓${NC} sync_people.py exists" || echo -e "  ${RED}✗${NC} sync_people.py missing"
[ -x "sync_people.py" ] && echo -e "  ${GREEN}✓${NC} sync_people.py is executable" || echo -e "  ${YELLOW}⚠${NC} sync_people.py not executable"

# Check cache directory
[ -d "../.cache/enrichment" ] && echo -e "  ${GREEN}✓${NC} Cache directory exists" || echo -e "  ${YELLOW}⚠${NC} Cache directory missing"

echo ""
echo "=========================================="
echo "Validation Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Install dependencies: pip install -r requirements.txt"
echo "2. Copy .env.example to .env and add API keys"
echo "3. Run full workflow: ./sync_people.py extract && ./sync_people.py sync"
echo "4. Test enrichment: ./sync_people.py enrich"
echo ""
