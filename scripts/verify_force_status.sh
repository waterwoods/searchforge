#!/usr/bin/env bash
#
# verify_force_status.sh
# Verify /ops/force_status endpoint is working correctly
# Exit 0 on success, 1 on failure
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Configuration
API_BASE="${API_BASE:-http://localhost:8001}"
FORCE_STATUS_URL="${API_BASE}/ops/force_status"

log_info "Verifying force_status endpoint at ${FORCE_STATUS_URL}"

# Test 1: Basic endpoint access
log_info "Test 1: Basic endpoint access (no params)"
RESPONSE=$(curl -s "${FORCE_STATUS_URL}")
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    log_error "Failed to connect to ${FORCE_STATUS_URL}"
    exit 1
fi

log_success "Successfully connected to endpoint"

# Test 2: Validate JSON response
log_info "Test 2: Validate JSON response structure"
echo "$RESPONSE" | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "Response is not valid JSON"
    echo "Response: $RESPONSE"
    exit 1
fi

log_success "Response is valid JSON"

# Test 3: Check required fields
log_info "Test 3: Check required fields"

REQUIRED_FIELDS=(
    ".force_override"
    ".hard_cap_enabled"
    ".planned_params"
    ".effective_params"
    ".precedence_chain"
    ".hard_cap_limits"
    ".force_params"
)

MISSING_FIELDS=()

for FIELD in "${REQUIRED_FIELDS[@]}"; do
    VALUE=$(echo "$RESPONSE" | jq -r "${FIELD}")
    if [ "$VALUE" == "null" ]; then
        MISSING_FIELDS+=("$FIELD")
    fi
done

if [ ${#MISSING_FIELDS[@]} -ne 0 ]; then
    log_error "Missing required fields: ${MISSING_FIELDS[*]}"
    exit 1
fi

log_success "All required fields present"

# Test 4: Check precedence_chain is array
log_info "Test 4: Validate precedence_chain is array"
CHAIN_TYPE=$(echo "$RESPONSE" | jq -r '.precedence_chain | type')
if [ "$CHAIN_TYPE" != "array" ]; then
    log_error "precedence_chain is not an array (got: $CHAIN_TYPE)"
    exit 1
fi

CHAIN_LENGTH=$(echo "$RESPONSE" | jq -r '.precedence_chain | length')
if [ "$CHAIN_LENGTH" -lt 3 ]; then
    log_error "precedence_chain too short (expected at least 3 steps, got: $CHAIN_LENGTH)"
    exit 1
fi

log_success "precedence_chain is valid array with $CHAIN_LENGTH steps"

# Test 5: Test with planned parameters
log_info "Test 5: Test with planned parameters"
PLANNED_JSON='{"num_candidates":100,"rerank_topk":50,"qps":60}'
PLANNED_RESPONSE=$(curl -s "${FORCE_STATUS_URL}?planned=$(echo -n "$PLANNED_JSON" | jq -Rr @uri)")

echo "$PLANNED_RESPONSE" | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "Response with planned params is not valid JSON"
    exit 1
fi

PLANNED_PARAMS=$(echo "$PLANNED_RESPONSE" | jq -r '.planned_params')
if [ "$PLANNED_PARAMS" == "{}" ] || [ "$PLANNED_PARAMS" == "null" ]; then
    log_error "planned_params not correctly parsed from query string"
    exit 1
fi

log_success "Planned parameters correctly processed"

# Test 6: Display full response for inspection
log_info "Test 6: Display sample response"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Sample Response (no params):"
echo "═══════════════════════════════════════════════════════════"
echo "$RESPONSE" | jq .
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Sample Response (with planned params):"
echo "═══════════════════════════════════════════════════════════"
echo "$PLANNED_RESPONSE" | jq .
echo ""

# Extract key info
FORCE_OVERRIDE=$(echo "$RESPONSE" | jq -r '.force_override')
HARD_CAP_ENABLED=$(echo "$RESPONSE" | jq -r '.hard_cap_enabled')
FORCE_PARAMS=$(echo "$RESPONSE" | jq -r '.force_params')
HARD_CAP_LIMITS=$(echo "$RESPONSE" | jq -r '.hard_cap_limits')

echo "═══════════════════════════════════════════════════════════"
echo "Current Configuration:"
echo "═══════════════════════════════════════════════════════════"
echo "Force Override:     ${FORCE_OVERRIDE}"
echo "Hard Cap Enabled:   ${HARD_CAP_ENABLED}"
echo "Force Params:       ${FORCE_PARAMS}"
echo "Hard Cap Limits:    ${HARD_CAP_LIMITS}"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test 7: Verify precedence chain content
log_info "Test 7: Verify precedence chain content"
CHAIN=$(echo "$RESPONSE" | jq -r '.precedence_chain | join("\n")')

# Check for expected markers
if ! echo "$CHAIN" | grep -q "START:"; then
    log_error "precedence_chain missing START marker"
    exit 1
fi

if ! echo "$CHAIN" | grep -q "END:"; then
    log_error "precedence_chain missing END marker"
    exit 1
fi

if ! echo "$CHAIN" | grep -q "FORCE_OVERRIDE:"; then
    log_error "precedence_chain missing FORCE_OVERRIDE step"
    exit 1
fi

if ! echo "$CHAIN" | grep -q "HARD_CAP:"; then
    log_error "precedence_chain missing HARD_CAP step"
    exit 1
fi

log_success "Precedence chain has all required markers"

# Display precedence chain
echo "═══════════════════════════════════════════════════════════"
echo "Precedence Chain:"
echo "═══════════════════════════════════════════════════════════"
echo "$CHAIN"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Final summary
log_success "All verification tests passed! ✅"
echo ""
echo "Endpoint:           ${FORCE_STATUS_URL}"
echo "Force Override:     ${FORCE_OVERRIDE}"
echo "Hard Cap:           ${HARD_CAP_ENABLED}"
echo "Tests Passed:       7/7"
echo ""

exit 0

