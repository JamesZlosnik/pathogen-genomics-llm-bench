# Session Log Template

> Copy this file into your run directory as `session_log.md` and fill it in during the run.
> Record exchanges verbatim where possible. This log is primary data for the benchmark.

---

## Run Metadata

| Field | Value |
|-------|-------|
| Date | |
| Project | |
| Prompt version | e.g. `PROMPT.md v1.0` or `PROMPT_nogrill.md v1.0` |
| Model | |
| Harness | |
| Provider | |
| Provider base URL | e.g. `http://localhost:8080` |
| Context window (tokens) | |
| Temperature | |
| Any other model params | |

---

## 1. Initial Prompt Delivered

> Paste the exact text sent to the model (should match the canonical prompt exactly).

```
<paste prompt here>
```

---

## 2. Planning Phase

> If the model produced a plan before writing code, paste it here verbatim.
> If the model skipped directly to code, write "No planning phase."

```
<paste model plan here>
```

### Your response to the plan (if any)

```
<paste your response here, or "Accepted without comment">
```

---

## 3. Grill / Clarification Phase

> Paste each clarifying question the model asked and your answer verbatim.
> If no questions were asked, write "No clarifying questions."

### Question 1

**Model:** 

**You:** 

### Question 2

**Model:** 

**You:** 

*(add more as needed)*

---

## 4. Execution Phase

> Describe what the model did during execution. Note any tool calls, file reads/writes,
> errors encountered, self-corrections, or retries. For harnesses that produce a transcript,
> attach or paste it below.

### Actions taken (summary)

- 
- 
- 

### Errors / self-corrections observed

- 

### Full transcript (if available)

```
<paste or attach harness transcript>
```

---

## 5. Final Output

> List every file produced by the model.

| File | Present | Non-empty | Notes |
|------|---------|-----------|-------|
| | ☐ | ☐ | |
| | ☐ | ☐ | |

---

## 6. Automated Test Results

```bash
# Command run:
pytest tests/ --output-dir runs/<run-id>/output/ -v

# Output:
<paste pytest output>
```

| Test | Pass/Fail |
|------|-----------|
| | |

---

## 7. Evaluator Notes

> Observations that don't fit neatly into the rubric. Domain errors, hallucinated tools,
> interesting planning behaviour, unexpected strengths, etc.

---

## 8. Scores

| Dimension | Score (0–4) | Notes |
|-----------|------------|-------|
| Correctness | | |
| Code Quality | | |
| Domain Appropriateness | | |
| Completeness | | |
| Autonomous Execution | | |
| **Total** | **/20** | |

**Automated tests:** `X / Y passed (Z%)`

**Time to completion:** minutes
