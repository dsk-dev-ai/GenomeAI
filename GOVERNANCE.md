# GenomeAI Governance

## Overview

GenomeAI follows a **tiered open-core governance model** inspired by Kubernetes and PostHog. The project is led by a core team of maintainers, with decision-making authority distributed across domain-specific committees.

## Roles

### Community Member

Anyone who uses GenomeAI, participates in discussions, or contributes in any way. All community members are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

### Contributor

A community member who contributes code, documentation, design, or other work via pull requests. Contributors gain no special authority but build reputation through quality contributions.

### Maintainer

A contributor who has demonstrated sustained, high-quality contributions and earned commit access. Maintainers are responsible for:

- Reviewing and merging pull requests
- Triaging and resolving issues
- Mentoring new contributors
- Maintaining code quality and test coverage
- Participating in governance discussions

**Appointment:** A contributor is nominated by an existing maintainer and confirmed by a supermajority (67%) of existing maintainers.

**Removal:** A maintainer may be removed by a supermajority vote if they are inactive for 6+ months or violate the Code of Conduct.

### Domain Committee

For specialized areas (Genomics, AI/ML, Security, UI/UX), a domain committee oversees design decisions and standards. Each committee has 3–5 members, at least one of whom is a maintainer.

### Technical Steering Committee (TSC)

The TSC is the highest decision-making body for the project. It consists of 5–7 members:

- 3 elected by maintainers (annual elections)
- 2 appointed by the core organization
- Up to 2 additional seats for community representatives

**Responsibilities:**

- Approve or reject major architectural changes
- Resolve disputes escalated from domain committees
- Define project roadmap and release scope
- Manage the project budget and resources
- Appoint and remove maintainers

## Decision-Making

### Lazy Consensus

Default decision-making mechanism. Proposals are announced with a minimum 7-day review period. If no objections are raised, the proposal passes. Any maintainer can block a proposal by raising a substantive objection.

### Voting

Used when lazy consensus cannot be reached. Requires a 7-day voting period. Supermajority (67%) of voting members required to pass.

## Roadmap Governance

See [ROADMAP.md](ROADMAP.md) for the current roadmap.

- Minor features: approved by domain committee
- Major features: approved by TSC
- Strategic pivots: requires 75% TSC approval + community discussion period (30 days)

## Release Process

1. Maintainers propose a release candidate.
2. Release candidate undergoes a 2-week testing period.
3. TSC votes to approve the release (simple majority).
4. Release is tagged and published.

## Conflict of Interest

All TSC members and maintainers must disclose conflicts of interest. Anyone with a conflict recuses themselves from related decisions.

## Code of Conduct Enforcement

The TSC appoints a Code of Conduct Committee of 3 neutral members to handle enforcement actions independently.

## Amendments to Governance

Changes to this governance document require:

1. A discussion period of at least 30 days.
2. Approval by 75% of the TSC.
3. Ratification by a public vote of all maintainers (simple majority).
