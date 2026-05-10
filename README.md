
# SENTINODE: The Visual Auditor IDE

> **Project Status: Proof of Concept (PoC)**  
> *Notice: This repository currently serves as the technical specification and roadmap. Core analysis engine code is in private R&D and will be pushed following the completion of Milestone 1.*

---

## 🛠 Project Overview
SENTINODE is an interactive, graph-based IDE designed to visualize smart contract logic, state transitions, and security risks. By unifying **Slither** and **Traverse** data into a **React Flow** canvas, it enables auditors to visually trace state transitions, call-graphs, and execution risks across any EVM-compatible protocol providing a human-readable "flight simulator" experience through a complex protocol logic.

### Beyond Glamsterdam
While initially optimized for the **Glamsterdam upgrade** (EIP-8037 and EIP-7928), SENTINODE is built as foundational infrastructure for permanent EVM security analysis.

## 🚀 Phase 1 Implementation (Current)
We are currently bridging the Logic Extraction Engine.
- [x] Slither CFG (Control Flow Graph) integration.
- [x] Traverse `sol2cg` call-graph mapping.
- [ ] Unified "Sentinode Manifest" JSON generator.

## 🗺 Roadmap
### 🟢 Milestone 1: Logic Extraction Engine (CLI Manifest Generator)
*The foundation of the SENTINODE auditor, converting raw Solidity IR into a high-fidelity data inventory.*

**Achievements thus far:**
*   **Holistic Project Organization**: 
    *   Automated workspace cleanup by migrating raw `.dot` files to `/generated_cfgs`.
*   **High-Precision Mapping**: 
    *   **Statement-Level Extraction**: Granular tracking of `internal` and `external` (High-Level) calls.
    *   **Contextual Events**: Argument extraction from high-level Solidity expressions rather than mangled IR.
    *   **Robust Error Handling**: Statement-anchored, de-duplicated `revert` tracking.
*   **Performance Optimization**: 
    *   Implementation of the `SENTINODE_MAP` keyed object, enabling **O(1) constant-time lookup** for the frontend.
*   **IP Protection**: 
    *   Transitioned to a **Proprietary Source-Available** license to protect the "Deep Trace" engine logic.
      
### 🟢 Milestone 2: Visual IDE Canvas (React Flow Alpha)
### 🟢 Milestone 3: Live Simulation & "Glow" Effect (Tenderly/Anvil Integration)
### 🟢 Milestone 4: Invariant Stress-Testing (Echidna Visualizer)

## 📄 License
All rights reserved.
