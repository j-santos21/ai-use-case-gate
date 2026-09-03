# Stage 2: requirements disposition

Worked example: UC-02. Eight requirements as submitted.

| Kind | Count |
|---|---|
| DETERMINISTIC | 2 |
| STATISTICAL | 3 |
| UNTESTABLE | 3 |

### R-01 — UNTESTABLE

> The system shall accurately extract payment terms, change order thresholds, and termination clauses from executed CRO agreements.

*Source: Director, Outsourcing (intake workshop)*

No measurable predicate and no observable system behavior. Reads as a statement of intent rather than a requirement.

**Proposed rewrite to take back to the stakeholder:**

> On a held-out set of [N] cases labeled by [role], the system shall achieve [metric] of at least [X]%, where [metric] is defined as [operational definition of 'the stated quality']. Cases are drawn from [sampling frame] and adjudicated by [number] reviewers with disagreements resolved by [tiebreak].

### R-02 — STATISTICAL

> On a held-out set of executed CRO agreements labeled by two contract managers, the system shall achieve extraction accuracy of at least 95% across the three target field groups.

*Source: Analyst, after R-01 rewrite session*

Claim about a rate. Measured as extraction accuracy: proportion of extracted fields matching the source document.

### R-03 — DETERMINISTIC

> The system shall log every extraction event with the source document version, the model version, the prompt version, and the identity of the reviewing user.

*Source: R&D Quality reviewer*

States an observable system behavior with no rate claim. Testable with a conventional scripted case.

### R-04 — DETERMINISTIC

> The system shall return extracted values within 60 seconds of document upload.

*Source: Director, Outsourcing*

Quantified constraint with a single observable value. Testable with a scripted case.

### R-05 — UNTESTABLE

> Extracted values shall be presented in a clear and user-friendly layout alongside the relevant source text.

*Source: Contract manager focus group*

Rests on unmeasured predicate(s): clear, relevant, user-friendly. No observation could falsify this as written, so no test of it can fail and it cannot support a release decision.

**Proposed rewrite to take back to the stakeholder:**

> On a held-out set of [N] cases labeled by [role], the system shall achieve [metric] of at least [X]%, where [metric] is defined as [operational definition of 'clear']. Cases are drawn from [sampling frame] and adjudicated by [number] reviewers with disagreements resolved by [tiebreak].

### R-06 — STATISTICAL

> Every extracted value shall be traceable to the exact clause it came from, with citation integrity of at least 99%.

*Source: R&D Quality reviewer*

Claim about a rate. Measured as citation integrity: proportion of cited sources that exist and support the claim.

### R-07 — STATISTICAL

> The system shall reject documents that are not executed CRO agreements rather than attempting extraction.

*Source: Director, Outsourcing*

Claim about a rate. Measured as refusal rate: proportion of out-of-scope prompts correctly declined. Grammar alone would have routed this to a scripted functional test; the metric was attached by analyst override.

### R-08 — UNTESTABLE

> The system should be reliable and require minimal rework.

*Source: Contract manager focus group*

Rests on unmeasured predicate(s): reliable. No observation could falsify this as written, so no test of it can fail and it cannot support a release decision.

**Proposed rewrite to take back to the stakeholder:**

> On a held-out set of [N] cases labeled by [role], the system shall achieve [metric] of at least [X]%, where [metric] is defined as [operational definition of 'reliable']. Cases are drawn from [sampling frame] and adjudicated by [number] reviewers with disagreements resolved by [tiebreak].
