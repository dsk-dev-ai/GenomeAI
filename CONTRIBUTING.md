# Contributing to GenomeAI

Thank you for your interest in contributing to GenomeAI. This document provides guidelines and workflows for contributing.

## Code of Conduct

All contributors must adhere to the [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and constructive.

## Getting Started

1. **Read the docs.** Start with [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md) to understand the project.
2. **Check the roadmap.** See [ROADMAP.md](ROADMAP.md) for active milestones.
3. **Pick an issue.** Look for issues labeled `good-first-issue` or `help-wanted`.
4. **Discuss first.** For significant changes, open a discussion or comment on an existing issue before writing code.

## Development Setup

See [docs/development/](docs/development/) for environment setup guides (coming soon).

```bash
git clone https://github.com/dsk-dev-ai/GenomeAI.git
cd GenomeAI
```

## Contribution Workflow

```
1. Fork the repository
2. Create a feature branch (git checkout -b feat/my-feature)
3. Make your changes
4. Write or update tests
5. Run the test suite (make test)
6. Run linting and type checking (make lint, make typecheck)
7. Commit with a descriptive message (see below)
8. Push to your fork
9. Open a Pull Request
```

### Branch Naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring |
| `perf/` | Performance improvement |
| `test/` | Adding or updating tests |
| `chore/` | Maintenance, dependencies, tooling |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<body (optional)>

<footer (optional)>
```

Examples:
```
feat(ingestion): add FASTQ streaming validation
fix(workflow): handle empty variant calls gracefully
docs(api): document cohort endpoint
```

## Pull Request Guidelines

- **One change per PR.** Keep PRs focused on a single concern.
- **Reference issues.** Use `Closes #123` or `Related to #456`.
- **Keep it small.** Large PRs are harder to review. Break them into logical steps.
- **Self-review.** Check your own diff before requesting review.
- **Respond to feedback.** Address review comments promptly or explain your reasoning.

### PR Review Criteria

- Correctness
- Test coverage (minimum 80% for new code)
- Performance (no regressions)
- Documentation (public APIs must be documented)
- Security (no introduction of vulnerabilities)

## Coding Standards

### Python

- Format with [Ruff](https://docs.astral.sh/ruff/).
- Type hints required for all public functions.
- Follow [PEP 8](https://peps.python.org/pep-0008/) and [PEP 484](https://peps.python.org/pep-0484/).

### Rust

- Format with `rustfmt`.
- All public items must have doc comments.
- `clippy` must pass without warnings.

### Documentation

- Use Markdown for all documentation.
- API documentation uses OpenAPI 3.1 (REST) and Protobuf comments (gRPC).
- Include docstrings on all public modules, classes, and functions.

## Testing

- Unit tests: `make test-unit`
- Integration tests: `make test-integration`
- End-to-end tests: `make test-e2e`
- All tests: `make test`

Tests must pass in CI before merging.

## Governance

This project follows the governance model outlined in [GOVERNANCE.md](GOVERNANCE.md).

## Questions?

- Open a [GitHub Discussion](https://github.com/dsk-dev-ai/GenomeAI/discussions)
- See [SUPPORT.md](SUPPORT.md) for more ways to get help
