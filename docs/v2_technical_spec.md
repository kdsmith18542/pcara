# PCARA v2: Unified Polyglot Analysis Engine
## Technical Specification

### 1. Executive Summary
PCARA (Polyglot Codebase Analyzer and Refactor Assistant) is transitioning from a distributed microservices model to a **Single Unified Library/Binary**. This shift optimizes for deterministic analysis, local-first performance, and zero-cost scaling. By focusing on the "connective tissue" between programming languages (FFI, APIs, shared headers), PCARA fills a critical gap in the static analysis market currently ignored by single-language tools.

---

### 2. Strategic Pivot: Unified Core
The move to a unified library eliminates the "Microservice Tax"—the latency, infrastructure costs, and complexity of orchestrating multiple containers.

#### Comparison: v1 vs. v2

| Feature | v1 (Microservices) | v2 (Unified Library) |
| :--- | :--- | :--- |
| **Architecture** | Go/Rust Microservices + Docker | Single Rust Library (Crate) |
| **Parsing** | Language-specific pods | In-process Tree-sitter instances |
| **Data Flow** | Network (JSON/gRPC) | In-Memory (Zero-copy pointers) |
| **Infrastructure Cost** | High (Server-side compute) | Low (Client-side execution) |
| **Privacy** | Code sent to cloud | Code stays local |

---

### 3. Core Engine Architecture
The engine is built as a modular Rust crate that can be compiled into a CLI tool, a WASM module for browsers, or a shared library (.so, .dll).

#### A. Parser Layer (Tree-sitter)
- **Uniform CST**: Uses Tree-sitter to generate Concrete Syntax Trees for all supported languages.
- **Incremental Parsing**: Allows PCARA to re-analyze only changed files during a dev session.

#### B. The "Bridge" Layer (The Unique Edge)
This is the custom logic that detects inter-language interactions:
- **Direct FFI**: Scans for `extern "C"`, `ctypes`, `cgo`, or `JNI` signatures.
- **Network Bridges**: Maps REST/gRPC definitions to implementations across service boundaries.
- **Data Serialization**: Matches Protobuf or Thrift schemas to generated code.

#### C. Dependency Graph (Petgraph)
- **Nodes**: Functions, Classes, Modules.
- **Edges**: "Calls," "Implements," "Inherits," or "Bridges to (Cross-Language)."

---

### 4. Migration & Reuse of v1 Assets
To avoid a "total rewrite," we will leverage the existing Go/Rust microservices by refactoring them into the unified core.

#### 4.1. Harvesting the Parsers
The Tree-sitter parsers used in the v1 pods are highly portable. Instead of running them in separate Docker containers, we will move the grammar bindings into the unified Rust core as sub-modules.

#### 4.2. Porting the Go/Rust Gateway Logic
The logic in the current Go/Rust gateway (routing, metadata handling) will be migrated:
- **Go Logic**: Use `cgo` to bridge existing Go functions into the Rust core, or rewrite critical routing logic into Rust for better performance.
- **Rust API Logic**: Move directly into the main library as the "entry point" for the CLI and WASM interfaces.

#### 4.3. Moving from Docker to Binary
Instead of containerizing the analysis engine, we will use Cargo to build a single static binary. This enables a `brew install pcara` experience, which is significantly lower friction than requiring `docker-compose`.

---

### 5. Growth & Success Strategies (Low Cost)

#### 5.1. "Local-First" Revenue Model
Charge for the **Insights Layer** (SaaS Dashboard) while keeping the **Analysis Engine** (CLI) free and local. This solves enterprise privacy concerns.

#### 5.2. "Blast Radius" Analysis
A high-value feature that calculates the impact of a change across languages (e.g., *"Changing this C++ header breaks 4 Python wrappers"*).

#### 5.3. WASM for Instant Demos
Compile the core to WebAssembly to allow "drag-and-drop" repo analysis on the marketing website with zero server-side costs.

---

### 6. Implementation Roadmap

| Phase | Focus | Deliverable |
| :--- | :--- | :--- |
| **Phase 1** | **Consolidation** | Move all Tree-sitter grammars into a single Rust crate. |
| **Phase 2** | **The Bridge** | Implement logic to link Python/C++ or Go/Rust dependencies. |
| **Phase 3** | **The CLI** | Build a basic CLI that outputs a JSON dependency map. |
| **Phase 4** | **The Web** | Build the SaaS dashboard to visualize the JSON maps. |
