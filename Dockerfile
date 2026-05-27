# ==========================================
# STAGE 1: THE COMPILER & BUILD CLEANROOM
# ==========================================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://foundry.paradigm.xyz | bash
ENV PATH="/root/.foundry/bin:${PATH}"
RUN foundryup

# Pre-compile the venv into an isolated root directory (/opt/env)
RUN python3 -m venv /opt/env && \
    /opt/env/bin/pip install --upgrade pip && \
    /opt/env/bin/pip install --no-cache-dir slither-analyzer

# ==========================================
# STAGE 2: THE SLIM PRODUCTION RUNTIME
# ==========================================
FROM python:3.11-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the lightweight binaries and pre-compiled venv from Stage 1
COPY --from=builder /root/.foundry /root/.foundry
COPY --from=builder /opt/env /opt/env

# Map Foundry globally into the system PATH
ENV PATH="/root/.foundry/bin:${PATH}"

# Force the container system PATH to prioritize the isolated venv binaries
ENV PATH="/opt/env/bin:${PATH}"

# Ingest workspace scripts
COPY . .
RUN chmod +x orchestrator.sh

EXPOSE 8545
CMD ["./orchestrator.sh"]
