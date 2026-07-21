# Development Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Node.js](https://nodejs.org/) | >= 20 | JavaScript runtime |
| [pnpm](https://pnpm.io/) | >= 9 | JavaScript package manager |
| [uv](https://docs.astral.sh/uv/) | >= 0.5 | Python package manager |
| [Python](https://www.python.org/) | >= 3.11 | Python runtime |
| [Docker](https://www.docker.com/) | 24+ | Infrastructure services |

### Installing Prerequisites

```bash
# Node.js (via fnm, nvm, or direct install)
fnm install 20

# pnpm
corepack enable && corepack prepare pnpm@9 --activate

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker
# See https://docs.docker.com/engine/install/
```

## Workspace Overview

GenomeAI uses a **monorepo** managed by [Turborepo](https://turbo.build/repo) and [pnpm](https://pnpm.io/).

```
GenomeAI/
├── apps/            # Runnable applications
│   ├── web/         # Web dashboard (Future: Next.js)
│   ├── api/         # REST API (Future: FastAPI)
│   ├── worker/      # Background jobs
│   ├── cli/         # Command-line interface
│   ├── desktop/     # Desktop application
│   └── mcp/         # MCP server
├── packages/        # Shared libraries
│   ├── config/      # Shared config presets
│   ├── types/       # Shared TypeScript types
│   ├── ui/          # UI component library
│   ├── sdk-ts/      # TypeScript SDK
│   ├── sdk-python/  # Python SDK
│   └── shared/      # Shared utilities
├── connectors/      # External service connectors
├── plugins/         # Community plugins
├── docker/          # Docker configuration
└── docs/            # Documentation
```

### JavaScript / TypeScript

Managed by pnpm workspaces. Each `apps/*` and `packages/*` directory is a workspace member.

### Python

Managed by uv workspaces. The `packages/sdk-python` directory is a workspace member.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dsk-dev-ai/GenomeAI.git
cd GenomeAI

# 2. Install all dependencies
make install

# 3. Start infrastructure services (PostgreSQL, Redis)
make infra-up

# 4. Verify the environment
make doctor
```

## Common Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make lint` | Run linters (Biome + Ruff) |
| `make format` | Format all code |
| `make test` | Run all tests |
| `make typecheck` | Run type checking |
| `make build` | Build all packages |
| `make clean` | Clean build artifacts |
| `make doctor` | Check environment |
| `make infra-up` | Start Docker services |
| `make infra-down` | Stop Docker services |

## Adding Dependencies

### TypeScript packages

```bash
pnpm add <package> --filter <workspace>
pnpm add -D <package> --filter <workspace>
```

### Python packages

```bash
uv add <package> --package genomeai-sdk
uv add --dev <package> --package genomeai-sdk
```

## IDE Setup

### VS Code

Recommended extensions:

- **Biome** (`biomejs.biome`) — Linting and formatting
- **Python** (`ms-python.python`) — Python support
- **Pyright** (`ms-pyright.pyright`) — Type checking
- **Docker** (`ms-azuretools.vscode-docker`) — Container management

Create `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "biomejs.biome",
    "ms-python.python",
    "ms-pyright.pyright",
    "ms-azuretools.vscode-docker"
  ]
}
```

## Troubleshooting

### pnpm install fails

Ensure you are using the correct pnpm version:

```bash
corepack enable && corepack prepare pnpm@9 --activate
```

### uv sync fails

Ensure you have Python 3.11+ installed:

```bash
python3 --version
uv python list
```

### Docker services don't start

Check Docker is running and ports are available:

```bash
docker info
make doctor
```
