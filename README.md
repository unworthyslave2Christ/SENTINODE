
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
1. **Milestone 1**: Logic Extraction Engine (CLI Manifest Generator)
2. **Milestone 2**: Visual IDE Canvas (React Flow Alpha)
3. **Milestone 3**: Live Simulation & "Glow" Effect (Tenderly/Anvil Integration)
4. **Milestone 4**: Invariant Stress-Testing (Echidna Visualizer)

## 📄 License
MIT License
