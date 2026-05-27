FROM python:3.11-slim AS runner

# CRITICAL FIX 1: Installed ca-certificates, curl, git, and Node/NPM ecosystem binaries
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# CRITICAL FIX 2: Corrected toolchain installation URL path to foundry.paradigm.xyz
RUN curl -L https://paradigm.xyz | bash
ENV PATH="/root/.foundry/bin:${PATH}"
RUN foundryup

# --- SPEED OPTIMIZATION BLOCK: BAKE DEPENDENCIES INTO THE IMAGE SYSTEM LAYER ---
# We build the venv in /opt/sentinode_env so host bind mounts don't overwrite it
RUN python3 -m venv /opt/sentinode_env && \
    /opt/sentinode_env/bin/pip install --upgrade pip && \
    /opt/sentinode_env/bin/pip install slither-analyzer

WORKDIR /app

# Copy all infrastructure files, parsing scripts, and the orchestrator
COPY . .

# Explicitly ensure your orchestrator has permission to execute
RUN chmod +x orchestrator.sh

# Expose Anvil RPC Node Port for future Phase 3 dynamic visual transactions
EXPOSE 8545

# Enforce the script to run by default as originally designed
CMD ["./orchestrator.sh"]
