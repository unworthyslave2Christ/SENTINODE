#!/bin/bash
# orchestrator.sh - Enforced Sequence for SENTINODE Local Engine Core
set -e

# Capture the exact directory where the script was triggered
BASE_DIR=$(pwd)

TARGET_DIR="$BASE_DIR"
SCRIPTS_DIR="$BASE_DIR"

echo "=== STEP 1: DETECT COMPILATION FRAMEWORK ==="
cd "$TARGET_DIR"
if [ -f "foundry.toml" ]; then
    echo "Foundry project detected. Building with Forge..."
    forge build --force
elif [ -f "hardhat.config.js" ] || [ -f "hardhat.config.ts" ]; then
    echo "Hardhat project detected. Running compilation..."
    npm install --legacy-peer-deps
    npx hardhat compile
else
    echo "Warning: No explicit configuration found. Trying forge..."
    forge build --force || true
fi

echo "=== STEP 2 & 3: PYTHON VIRTUAL ENVIRONMENT ==="
cd "$SCRIPTS_DIR"
python3 -m venv env

# CRITICAL FIX: Explicitly source using absolute shell mapping path structures
# This guarantees that the subshell environment path registers the venv
source "$SCRIPTS_DIR/env/bin/activate"

echo "=== STEP 4: ENFORCING SLITHER PROVISIONING INSIDE VENV ==="
# Explicitly target the virtual environment's pip directly to guarantee isolation
"$SCRIPTS_DIR/env/bin/pip" install --upgrade pip
"$SCRIPTS_DIR/env/bin/pip" install slither-analyzer

echo "=== STEP 6: EXECUTING ANALYSIS & STATIC GENERATION ==="
cd "$TARGET_DIR"
# Use the virtual environment's explicit slither binary path so path lookups don't fail
"$SCRIPTS_DIR/env/bin/slither" . --print cfg
"$SCRIPTS_DIR/env/bin/slither-flat" . --strategy OneFile

echo "=== STEP 7: RUNNING JAVASCRIPT CFG SUB-PROCESSOR ==="
cd "$SCRIPTS_DIR"
# Invoked right after slither generation, but before the master python core
node processAllCfgs.js

echo "=== STEP 8: INVOKING SENTINODE MASTER ENGINE ==="
# Execute your core script using the explicit virtual environment python interpreter
"$SCRIPTS_DIR/env/bin/python3" sentinode-complete-core9.py

echo "=== PIPELINE COMPLETE: SCHEMA GENERATED SUCCESSFULLY ==="
