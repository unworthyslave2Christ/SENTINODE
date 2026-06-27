#!/bin/bash
# orchestrator.sh - Flexible Path Isolation Engine (Zero Network Fast-Path)
set -e

# Use the first argument as the working directory; default to current path if empty
WORK_DIR=${1:-$(pwd)}

TARGET_DIR="$WORK_DIR"
SCRIPTS_DIR="$(pwd)" # Scripts remain at the container's root install boundary

echo "=== STEP 1: DETECT COMPILATION FRAMEWORK ==="
cd "$TARGET_DIR"
if [ -f "foundry.toml" ]; then
    echo "Foundry project detected. Building with Forge..."
    forge build --force
elif [ -f "hardhat.config.js" ] || [ -f "hardhat.config.ts" || 'package.json' ]; then
    echo "Hardhat project detected. Running compilation..."
    npm install --legacy-peer-deps
    npx hardhat compile
else
    echo "Warning: No explicit configuration found. Trying forge..."
    forge build --force || true
fi

echo "=== STEP 2 & 3: PYTHON VIRTUAL ENVIRONMENT ==="
cd "$SCRIPTS_DIR"

# PRIORITY 1: Check for the container's pre-baked immutable system environment
if [ -f "/opt/sentinode_env/bin/activate" ]; then
    echo "✓ Pre-baked container environment detected at /opt/sentinode_env."
    ACTIVE_VENV_PATH="/opt/sentinode_env"
# PRIORITY 2: Fallback to local workspace env (for native host execution outside Docker)
else
    if [ ! -f "$SCRIPTS_DIR/env/bin/activate" ]; then
        echo "Virtual environment not detected. Initializing local workspace env..."
        python3 -m venv env
    else
        echo "Existing local workspace virtual environment detected."
    fi
    ACTIVE_VENV_PATH="$SCRIPTS_DIR/env"
fi

# Explicitly source using the resolved absolute environment path structure
source "$ACTIVE_VENV_PATH/bin/activate"

echo "=== STEP 4: ENFORCING SLITHER PROVISIONING INSIDE VENV ==="
# FAST-PATH CHECK: Skip running pip entirely if slither exists in the active venv
if [ -f "$ACTIVE_VENV_PATH/bin/slither" ]; then
    echo "✓ Slither binary already provisioned inside active venv. Bypassing network downloads."
else
    echo "Slither binary missing from active venv. Initializing dependency layer download..."
    "$ACTIVE_VENV_PATH/bin/pip" install --upgrade pip
    "$ACTIVE_VENV_PATH/bin/pip" install slither-analyzer
fi

echo "=== STEP 6: EXECUTING ANALYSIS & STATIC GENERATION ==="
cd "$TARGET_DIR"
# Use the resolved environment's explicit slither binary path so path lookups don't fail
"$ACTIVE_VENV_PATH/bin/slither" . --print cfg
"$ACTIVE_VENV_PATH/bin/slither-flat" . --strategy OneFile

echo "=== STEP 7: RUNNING JAVASCRIPT CFG SUB-PROCESSOR ==="
cd "$SCRIPTS_DIR"
# Pass the explicit target directory path down to your processing script
node processAllCfgs.js "$TARGET_DIR"

echo "=== STEP 8: INVOKING SENTINODE MASTER ENGINE ==="
# Execute your core script using the explicit virtual environment python interpreter
"$ACTIVE_VENV_PATH/bin/python3" sentinode-complete-core9.py "$TARGET_DIR"

echo "=== PIPELINE COMPLETE: SCHEMA GENERATED SUCCESSFULLY ==="
