# Evaluation Rubric

Each run is scored across five dimensions. Scores are integers 0–4. A total score of 20 is perfect; ≥14 is considered "usable with review"; <10 is "not usable."

Record scores in `scorecard_template.csv` and notes in the run's `evaluation.md`.

---

## Dimensions

### 1. Correctness (0–4)
Does the output produce the right answer / result?

| Score | Criteria |
|-------|----------|
| 4 | All outputs correct; passes all automated tests |
| 3 | Minor numerical or formatting errors; results interpretable and usable with small fixes |
| 2 | Partially correct; core logic right but meaningful errors in ≥1 component |
| 1 | Mostly wrong but shows domain understanding; requires substantial rework |
| 0 | Completely wrong, crashes, or hallucinates domain-specific content (fake tools, fake gene names, etc.) |

### 2. Code Quality (0–4)
Is the code readable, idiomatic, and maintainable?

| Score | Criteria |
|-------|----------|
| 4 | Clean, idiomatic, well-commented; follows conventions for the language/tool |
| 3 | Mostly clean; minor style issues; adequately commented |
| 2 | Functional but messy; little/no comments; non-idiomatic |
| 1 | Works but is hard to follow; significant technical debt |
| 0 | Broken, unrunnable, or so tangled it must be rewritten |

### 3. Domain Appropriateness (0–4)
Does the solution reflect knowledge of pathogen genomics / public health bioinformatics?

| Score | Criteria |
|-------|----------|
| 4 | Uses correct tools, formats, thresholds, and terminology; no hallucinated biology |
| 3 | Mostly appropriate; one minor domain error or missed convention |
| 2 | Generic solution that works but ignores domain conventions (e.g. wrong file format assumptions, wrong defaults) |
| 1 | Domain errors that would mislead or produce incorrect biological conclusions |
| 0 | Hallucinated tools, genes, or methods that do not exist |

### 4. Completeness (0–4)
Did the model produce everything asked for?

| Score | Criteria |
|-------|----------|
| 4 | All requested outputs present and correct |
| 3 | Minor omissions; 1 small deliverable missing |
| 2 | Several components missing; core deliverable present |
| 1 | Only a partial skeleton or stub delivered |
| 0 | No usable output |

### 5. Autonomous Execution (0–4)
How much human intervention was needed to get a working result?

| Score | Criteria |
|-------|----------|
| 4 | Ran first time with no edits; fully autonomous |
| 3 | Required 1–2 minor fixes (typo, wrong path, one missing import) |
| 2 | Required moderate debugging; 3–5 interventions |
| 1 | Required substantial hand-holding; model stalled or looped |
| 0 | Could not complete the task even with assistance |

---

## Automated Test Pass Rate

In addition to the rubric, record the automated test pass rate where tests exist:

`tests_passed / tests_total` → expressed as a fraction and percentage.

This is the most objective signal and should be weighted heavily in comparisons.

---

## evaluation.md Template

```markdown
# Run Evaluation

**Date:** YYYY-MM-DD
**Model:** 
**Harness:** 
**Provider:** 
**Project:** 

## Scores

| Dimension | Score (0–4) |
|-----------|------------|
| Correctness | |
| Code Quality | |
| Domain Appropriateness | |
| Completeness | |
| Autonomous Execution | |
| **Total** | **/20** |

## Automated Tests
`X / Y passed (Z%)`

## Notes
<!-- What did the model do well? Where did it fail? Any hallucinations? -->

## Notable Issues
<!-- List specific bugs, wrong tool invocations, hallucinated biology, etc. -->

## Time to Completion
<!-- Wall clock time from prompt to final output -->
```
