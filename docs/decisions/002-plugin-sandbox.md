# ADR 002: Plugin Sandbox Architecture

**Status:** Accepted

## Context

The plugin system must allow community-contributed code to extend the platform safely. Plugins may contain bugs or malicious code. The sandbox must prevent plugins from compromising other plugins, core services, or the host system.

## Decision

Use OCI containers as the plugin sandbox runtime.

### Key Design Choices

- Each plugin runs in its own container with resource limits (CPU, memory, filesystem).
- Plugins communicate with core services via the hook API over localhost HTTP/gRPC.
- Plugin containers have no network access to external services unless explicitly granted.
- The filesystem is read-only except for a dedicated output volume.
- Plugin images are signed and their digests are verified before execution.
- The plugin registry stores image digests for audit trail.

## Consequences

**Positive:**
- Strong isolation between plugins and core.
- Resource limits prevent runaway plugins.
- Existing container security tools (seccomp, AppArmor) provide additional hardening.
- Plugin developers can use any language or toolchain within their container.

**Negative:**
- Container startup latency for short-lived plugin invocations.
- Storage overhead for plugin container images.
- More complex debugging experience for plugin developers.

## Alternatives Considered

1. **WebAssembly (Wasm) sandbox** — Lower overhead, but limited library support and no GPU access for ML plugins.
2. **Unix process sandboxing (seccomp, Landlock)** — Lighter weight, but weaker isolation guarantees.
3. **Python virtual environments** — Insufficient isolation for untrusted code.
