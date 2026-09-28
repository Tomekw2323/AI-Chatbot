# 0001. Record architecture decisions

- Status: Accepted
- Date: 2026-09-28

## Context

The product owner is not a developer; an experienced developer supervises the code, and AI coding
agents contribute. Everyone needs to know *why* the system looks the way it does, not just *what*
it is.

## Decision

Keep numbered ADRs in `docs/adr/`. Every decision that is expensive to reverse (framework, data
model shape, hosting, module boundaries, security/GDPR posture) gets an ADR. ADRs are immutable
once accepted; changes are made by a new ADR that supersedes the old one.

## Consequences

- Reviewers can challenge decisions explicitly (the initial set is marked "Proposed").
- Small overhead per significant change; PR template/CONTRIBUTING asks whether an ADR is needed.
