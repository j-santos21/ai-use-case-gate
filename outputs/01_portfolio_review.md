# Stage 1: portfolio intake review

13 requests, scored against the intake rubric. Value and
evidence cost are both on a 0-100 scale; margin is value minus cost.
Binding constraint names the evidence factor contributing most above
its floor, which is the thing to change if the use case is to move.

| ID | Use case | Function | Value | Evidence cost | Margin | Disposition | Binding constraint |
|---|---|---|---|---|---|---|---|
| UC-02 | CRO contract term extraction into the vendor register | R&D Procurement | 68 | 8 | +60 | **BUILD** | consequence_of_error (2/5) |
| UC-01 | Protocol deviation triage and severity pre-classification | Clinical Operations | 75 | 38 | +38 | **BUILD** | consequence_of_error (3/5) |
| UC-04 | Clinical study report patient narrative drafting | Medical Writing | 75 | 56 | +19 | **PILOT** | consequence_of_error (4/5) |
| UC-05 | Internal R&D policy and SOP question answering | R&D Quality | 42 | 26 | +16 | **PILOT** | consequence_of_error (3/5) |
| UC-10 | Governance board minutes and action item extraction | R&D Portfolio Management | 32 | 20 | +12 | **PILOT** | ground_truth (3/5) |
| UC-07 | Site feasibility questionnaire first-pass responses | Clinical Operations | 42 | 31 | +11 | **PILOT** | ground_truth (3/5) |
| UC-03 | Literature screening for safety signal candidates | Pharmacovigilance | 74 | 62 | +11 | **PILOT** | consequence_of_error (5/5) |
| UC-06 | Adverse event case coding to MedDRA preferred terms | Pharmacovigilance | 66 | 56 | +10 | **PILOT** | consequence_of_error (5/5) |
| UC-11 | Target hypothesis generation from internal and public datasets | Discovery Research | 58 | 51 | +6 | **REFRAME** | ground_truth (5/5) |
| UC-09 | SOP change impact analysis across the document hierarchy | R&D Quality | 50 | 50 | +0 | **PILOT** | consequence_of_error (4/5) |
| UC-12 | Lab notebook semantic search across legacy archives | Discovery Research | 34 | 44 | -10 | **REFRAME** | ground_truth (4/5) |
| UC-08 | Investigator brochure section drafting from source studies | Medical Writing | 59 | 75 | -16 | **REFRAME** | consequence_of_error (4/5) |
| UC-13 | First-line review of informed consent form translations | Clinical Operations | 18 | 75 | -58 | **DECLINE** | consequence_of_error (5/5) |

## Disposition counts

- BUILD: 2
- PILOT: 7
- REFRAME: 3
- DECLINE: 1

## Rationale by use case

**UC-01 — Protocol deviation triage and severity pre-classification** (BUILD)

Value clears the cost of proving it works with room to spare. Proceed to requirements and eval design.

**UC-02 — CRO contract term extraction into the vendor register** (BUILD)

Value clears the cost of proving it works with room to spare. Proceed to requirements and eval design.

**UC-03 — Literature screening for safety signal candidates** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-04 — Clinical study report patient narrative drafting** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-05 — Internal R&D policy and SOP question answering** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-06 — Adverse event case coding to MedDRA preferred terms** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-07 — Site feasibility questionnaire first-pass responses** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-08 — Investigator brochure section drafting from source studies** (REFRAME)

No defensible ground truth and no practical human check. There is no acceptance criterion that could fail, so there is no release decision to make. Narrow the scope to a slice that has a checkable answer, or accept it as an unvalidated assistive tool with no process dependency.

**UC-09 — SOP change impact analysis across the document hierarchy** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-10 — Governance board minutes and action item extraction** (PILOT)

Value and evidence cost are close. Run a bounded pilot with a real eval set before committing to a validated build; the pilot is there to move one of the two numbers, not to demo the model.

**UC-11 — Target hypothesis generation from internal and public datasets** (REFRAME)

No defensible ground truth and no practical human check. There is no acceptance criterion that could fail, so there is no release decision to make. Narrow the scope to a slice that has a checkable answer, or accept it as an unvalidated assistive tool with no process dependency.

**UC-12 — Lab notebook semantic search across legacy archives** (REFRAME)

Evidence cost exceeds value at the current scope. Either narrow the scope to lower the evidence burden or find the higher-volume version of the same problem.

**UC-13 — First-line review of informed consent form translations** (DECLINE)

Evidence cost substantially exceeds value. Declining here is the cheap decision; declining after six months of pilot is not.
