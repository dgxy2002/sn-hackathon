# E09 Backlog - Productionisation and Security

**Epic:** [E09 - Productionisation and Security](../epics/E09-productionisation-and-security.md)
**Owner:** Tim
**Posture:** All tickets are deferred until the POC is validated. Baseline secret hygiene and synthetic-data use still apply now.

## POC baseline evidence

The deferred ticket statuses remain unchanged. Current safeguards are limited to
repository-wide `.env` and generated-secret ignores, a safe `.env.example`,
startup rejection of wildcard origins and unconfigured live model modes,
secret-free health output, synthetic-only policy fixtures, escaped response
content, and frontend allowlists for action targets and citation URLs. These are
POC guardrails, not production identity, privacy, threat-model, or operational
hardening evidence.

## E09-T01 - Threat-model the intended production system

| Field | Value |
|---|---|
| Status | Deferred |
| Priority | P3 |
| Size | M |
| Depends on | Validated POC architecture |

**User story:** As a future service owner, I need an agreed threat model so production controls address the actual identity, document, agent, retrieval, and model risks.

**Requirements:** URS-NFR-008, URS-NFR-014; PRD-NFR-007, PRD-NFR-019.

**Acceptance criteria:**

- [ ] Assets, trust boundaries, actors, abuse cases, and mitigations are reviewed.
- [ ] Agent tools, prompt injection, data exfiltration, and model-provider exposure are covered.
- [ ] Residual risks have accountable owners.

## E09-T02 - Implement production identity and data lifecycle

| Field | Value |
|---|---|
| Status | Deferred |
| Priority | P3 |
| Size | L |
| Depends on | E09-T01, legal and privacy review |

**User story:** As a real customer, I need my identity and policy data isolated, encrypted, retained appropriately, and deletable.

**Requirements:** URS-NFR-005, URS-NFR-008; PRD-NFR-004, PRD-NFR-007.

**Acceptance criteria:**

- [ ] Authentication, authorization, tenant isolation, and session controls are tested.
- [ ] Data is encrypted in transit and at rest.
- [ ] Retention, export, correction, and deletion workflows are tested.
- [ ] Audit logs avoid policy contents and sensitive profile values.

## E09-T03 - Harden secrets, deployment, and operations

| Field | Value |
|---|---|
| Status | Deferred |
| Priority | P3 |
| Size | L |
| Depends on | E09-T01 |

**User story:** As an operator, I need controlled deployment and recovery so the service can be monitored and restored without exposing credentials.

**Requirements:** URS-NFR-008; PRD-NFR-007.

**Acceptance criteria:**

- [ ] The POC Secrets Manager mapping is hardened with least-privilege access, rotation, auditing, and recovery procedures.
- [ ] Deployment, rollback, backup, restore, monitoring, alerting, and incident procedures are tested.
- [ ] Dependency, container, and infrastructure scans meet agreed gates.
- [ ] Availability, latency, and cost targets are defined and measured.

## E09-T04 - Complete regulatory and production validation

| Field | Value |
|---|---|
| Status | Deferred |
| Priority | P3 |
| Size | L |
| Depends on | E09-T02, E09-T03 |

**User story:** As the organization launching the service, we need legal, privacy, security, and financial-regulation approval before using real customer data or influencing real transactions.

**Requirements:** URS-NFR-008; PRD-NFR-007.

**Acceptance criteria:**

- [ ] Singapore legal, privacy, and financial-regulation reviews approve scope and wording.
- [ ] Penetration, resilience, load, recovery, and accessibility tests meet agreed targets.
- [ ] Product claims, conflicts, source coverage, and complaint handling are documented.
- [ ] A launch decision records accepted risks and accountable sign-off.