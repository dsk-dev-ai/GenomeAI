# Security Policy

## Supported Versions

This project is in early development. No stable releases have been published yet. Security updates will be provided for the latest stable release once available.

## Reporting a Vulnerability

We take the security of GenomeAI seriously. If you discover a security vulnerability, please report it privately before disclosing it publicly.

**Do not report security vulnerabilities through public GitHub issues.**

### Contact

Report vulnerabilities privately by opening a [GitHub Security Advisory](https://github.com/dsk-dev-ai/GenomeAI/security/advisories/new).

### What to Include

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested mitigation (if known)

### Response Timeline

We will acknowledge receipt within 5 business days and provide an initial assessment within 14 days. Fix timelines depend on severity and project capacity.

### Disclosure Policy

We follow coordinated disclosure:

1. Reporter submits vulnerability privately.
2. We confirm and develop a fix.
3. We release a patched version.
4. We publish an advisory 30 days after the fix is released.

## Security Design Principles

GenomeAI is built with the following security principles:

- **Least Privilege** — Components run with the minimum permissions required.
- **Defense in Depth** — Multiple layers of security controls.
- **Secure Defaults** — Safe configuration out of the box.
- **Fail Secure** — Errors default to denying access.
- **Auditability** — All security-relevant events are logged.
- **Encryption at Rest and in Transit** — Data is encrypted everywhere.

## Planned Security Features

The following are planned for implementation but not yet available:

- Attribute-based access control (ABAC)
- mTLS for service-to-service communication
- Audit logging with immutable storage
- Differential privacy primitives
- Container image signing
- Dependency vulnerability scanning
- Signed commits for maintainers

## Vulnerability Disclosure Policy

If you believe you have found a security vulnerability, please follow the reporting process above. We appreciate your help in keeping GenomeAI and its users safe.

## Related Documents

- [GOVERNANCE.md](GOVERNANCE.md) — Security team roles and responsibilities.
- [docs/deployment/](docs/deployment/) — Deployment security configuration (coming soon).
- [docs/development/](docs/development/) — Secure coding guidelines (coming soon).
