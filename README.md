# SENTINODE: The Visual Auditor IDE

> **Project Status: Core Logic Engine Completed (Phase 1 Baseline Verified)**


| 📂 Source Files Tracked | 🏗️ Total Contracts Parsed | 🎯 Deployment Accuracy | ⚡ Lookup Speed |
| :--- | :--- | :--- | :--- |
| **Fully Synchronized** | **16 / 16 (100% Match)** | **AST Lineage Enforced** | **O(1) Constant-Time** |

---

## 🛠️ Project Overview
SENTINODE is an interactive, graph-based security IDE designed to convert low-level abstract syntax trees (AST) and smart contract storage configurations into a fluid, visual auditing dashboard. By unifying Slither's complete core printing pipelines directly into a containerized Web3 visual layout canvas, SENTINODE gives security researchers a human-readable "flight simulator" experience to trace data dependencies, analyze variable updates, and map invariant vectors across complex multi-contract EVM protocols.

### Blending Remix Web3 Versatility & VS Code Workspace Power
* **Monaco Editor Sidecars**: Implements Microsoft's production code editing engine alongside visual logic flows. Selecting an interactive node automatically scrolls the compiler view down to the exact matching lines of code.
* **Live Provider Networks**: Pairs runtime browser wallet injections (MetaMask) or local sandbox networks (Anvil) with static dependency tracking to highlight storage layout alterations on demand.

---

## 🚀 Architectural Blueprint (Next.js + Docker Sandbox)
SENTINODE avoids fragile frontend text parsing by offloading analysis tasks to a sandboxed Docker engine environment. Security binaries run inside an immutable, isolated workspace, streaming data directly to a Next.js client engine application layer.

---

## 🗺️ Engineering Roadmap & Current Milestones

### 🟢 Milestone 1: The Unified Logic Extraction Engine
*Completed baseline verification. This compiler subsystem executes Slither AST hooks natively and pairs data streams with statement-level graph layouts to synthesize a standalone visual audit manifest.*

*   **100% Core Footprint Cataloguing**: Loops through all compiled modules un-opinionatedly, bringing background lineage layers, libraries, interfaces, and unique target contracts (like `SlitherTest` and `SlitherRequireContract`) straight into the master data pool.
*   **Sibling-Enhanced Splicing Layouts**: Injects parent contract metadata prefixes (`ParentContract-Variable`) into your arrays (`storage_reads_enhanced`, `storage_writes_enhanced`, and `state_variables_written_enhanced`) to give your graph connectors exact mapping targets.
*   **O(1) Constant-Time CFG Splicing**: Integrates statement-level trace maps using your exact `.dot` filename signature parameters (`.-Contract-func(args).dot`). This injects unpruned, multi-line execution blocks right into function profiles with zero lookup delay.
*   **Streamlined Graph Architectures**: Filters out duplicate tracking metrics (`storage_reads`, `storage_writes`, etc.) from inside `cfg_deep_trace` to minimize memory usage, while safely preserving critical evaluation variables like `is_a_view_function`.
*   **Lineage-Aware Intake Metrics**: Implements specific base template checking routines to isolate and filter out `forge-std` test scripts without dropping actual user code, ensuring your run metadata remains accurate.

### 🟡 Milestone 2: Visual IDE Canvas (Next.js + React Flow Alpha) — *CURRENT PHASE*
*Transforming unified master schemas into a fluid frontend graph dashboard.*
*   **Dagre Graph Layout Layouts**: Passing measure arrays and dependency edges through Dagre to compute `x` and `y` bounding box boundaries automatically, preventing visual node overlapping.
*   **Interactive Node States**: Mapping `is_state_changing_entry_point` attributes directly to dynamic Tailwind CSS styles to highlight primary entry points with a green glow border.
*   **GitHub Repository Ingestion**: Ingests public or private code repositories seamlessly via authenticated clone workers, scanning for `foundry.toml` settings immediately upon synchronization.

### ⚪ Milestone 3: Live Simulation & "Glow" Effect (Anvil Integration)
*   Connecting runtime JSON-RPC execution networks directly to your visual nodes, flashing lines on the canvas to track active storage mutations in real time.

### ⚪ Milestone 4: Invariant Stress-Testing (Echidna Visualizer)
*   Leveraging `impacts_functions_enhanced` data relationships to generate fuzzing sequences dynamically from custom visual canvas node selections.

---

## 📦 Getting Started

### Prerequisites
* Docker & Docker Compose
* Node.js v18+

### Initialization
1. Spin up the sandboxed toolbox network containers:
   ```bash
   docker-compose up -d --build
   ```
2. Run the master data compilation engine script to synthesize the workspace configuration:
   ```bash
   python3 sentinode_complete_core.py
   ```
3. Start the Next.js visual IDE development server:
   ```bash
   npm run dev
   ```

---

## 📄 License
Proprietary Source-Available License. All rights reserved. Intellectual property protections apply to the core "Deep Trace" AST parsing module and visual orchestration systems.
