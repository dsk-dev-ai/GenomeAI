# ADR 004: Attribute-Based Access Control Over RBAC

**Status:** Accepted

## Context

Genomic data access is complex. A researcher may have access to samples from study A but not study B, may view variant calls but not raw sequencing data, and may have temporary access granted via a data use agreement. Role-based access control (RBAC) is too coarse for these requirements.

## Decision

Implement Attribute-Based Access Control (ABAC) as the primary authorization model.

### Key Attributes

- **Subject attributes:** User ID, institutional affiliation, role, security clearance.
- **Resource attributes:** Study ID, consent code, data type, sensitivity level, owner institution.
- **Environment attributes:** Time of day, network origin, device posture.
- **Action attributes:** Read, write, delete, share.

### Policy Engine

Policies are expressed as declarative rules using Open Policy Agent (OPA) / Rego:

```
allow {
    input.subject.role == "researcher"
    input.resource.consent_code == "GRU"
    input.action == "read"
    input.environment.network == "trusted"
}
```

## Consequences

**Positive:**
- Fine-grained access control matching real-world genomic data governance.
- Policies can be authored and audited independently of code.
- OPA/Rego is widely adopted with good tooling.

**Negative:**
- More complex policy authoring than RBAC.
- Performance overhead of policy evaluation on every request (mitigated by caching).
- Requires tooling for policy testing and validation.

## Alternatives Considered

1. **RBAC with scopes** — Added complexity without solving the granularity problem.
2. **ReBAC (Relationship-Based)** — Better for social graphs; over-engineered for genomic access patterns.
3. **Custom policy engine** — Unnecessary; OPA is mature and well-suited.
