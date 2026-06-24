# Contributing to pathogen-genomics-llm-bench

Thank you for your interest in contributing. This document explains how to submit
run results, propose new projects, and report issues with existing prompts.

---

## What this repo is (and isn't)

**In scope:**
- Benchmark run results using the existing project prompts
- New project briefs that test realistic pathogen genomics / public health bioinformatics tasks
- Improvements to the test suite, fixture generator, or scoring rubric
- Setup documentation for providers and harnesses
- Bug reports on prompt ambiguities or incorrect ground-truth fixtures

**Out of scope:**
- General Python/R/Nextflow tutorials unrelated to pathogen genomics
- Model fine-tuning or training scripts
- Web scraping, data acquisition, or access to non-public genomic data
- Projects that require proprietary tools or non-open databases

If you are unsure whether something is in scope, open an issue before writing code.

---

## 1. Submitting a Run Result

Run results are the primary scientific contribution. A result is a completed benchmark
run of a model+harness+provider combination on one or more projects.

### What to submit

A pull request adding a new directory under `runs/` containing:

```
runs/YYYY-MM-DD_<model>_<harness>_<provider>_<project_id>/
├── prompt.md          # Which prompt file was used (PROMPT.md or PROMPT_nogrill.md)
│                      # and any deviations from it (there should be none)
├── session_log.md     # Filled-in session log (see runs/session_log_template.md)
├── evaluation.md      # Rubric scores and notes
└── output/            # All files produced by the model
    ├── <script>.py    # (or .R, .nf, etc.)
    └── ...
```

Also add one row to `scoring/scorecard_template.csv` with your run's scores.

### Naming convention

`YYYY-MM-DD_<model>_<harness>_<provider>_<project_id>`

Examples:
- `2025-09-01_gemma4-27b_opencode_mlx_01`
- `2025-09-01_llama3.3-70b_claudecode_llamacpp_04`

Use lowercase, hyphens only, no spaces. Model names should include parameter count
and any relevant variant (e.g. `gemma4-27b` not just `gemma4`).

### Run metadata requirements

Your `session_log.md` must record:
- Exact model name and quantization (e.g. `Gemma4-27B-Instruct-Q4_K_M`)
- Provider and version or commit hash (for llama.cpp, include the git commit)
- Harness version
- Temperature and any other non-default generation parameters
- Context window configured
- Which prompt version was used (`PROMPT.md v1.0`)
- Time to completion

### What not to include in run outputs

- No patient data, real sample IDs, or internal institutional data
- No API keys, tokens, or credentials
- No files over 10 MB (large outputs should be summarised or truncated)
- FASTQ, BAM, VCF, and FASTA files are excluded by `.gitignore` — do not force-add them

### Automated tests

Before submitting, run the test suite against your output:

```bash
# Generate fixtures if you haven't already
python tests/generate_fixtures.py

# Run tests pointing at your output directory
pytest tests/ --output-dir runs/<your-run-dir>/output/ -v
```

Include the pytest output in your `session_log.md`.

---

## 2. Proposing a New Project

New projects must meet the following criteria:

### Criteria for acceptance

1. **Domain relevance** — the task must reflect a real workflow step in pathogen
   genomics or public health microbiology. "Write a Python script that reads a CSV"
   is not in scope. "Parse Nextclade JSON output and extract clade assignments and
   QC flags" is.

2. **Verifiable ground truth** — there must be a way to objectively check whether
   the output is correct. Preferred: automated tests against known-correct fixture
   data. Acceptable: a clearly specified expected output format with documented
   invariants (e.g. matrix symmetry, column names, value ranges).

3. **Not redundant** — check existing projects before proposing. We do not need
   multiple AMR parsers or multiple QC filter scripts. If you want to extend an
   existing project, propose a variant prompt instead.

4. **Self-contained** — the prompt must specify all inputs and outputs explicitly.
   A model should be able to complete the task from the prompt alone without
   access to external documentation.

5. **Prompt quality** — follow the prompt style of existing projects:
   - Clear numbered requirements
   - Explicit tool constraints (e.g. "use `cyvcf2` for VCF parsing")
   - Explicit `Input:` and `Output:` section at the end
   - No ambiguity about what constitutes a passing output

### How to propose

Open a GitHub issue using the **"New project proposal"** template (coming soon).
Include:
- A draft `BRIEF.md` describing the task in plain English
- A draft `PROMPT.md` following the existing format
- The difficulty tier you would assign it and why
- What you would test in the automated suite

Once the issue is approved, submit a PR adding the project folder.

### Prompt versioning rules

- New prompts start at `v1.0`
- **Never edit a prompt that has been used in a submitted run.** Edit a prompt
  after runs exist and those runs become incomparable.
- If a prompt needs correction, create `v1.1` in a new file and document the
  change in `docs/prompt_changelog.md`
- The original version is never deleted

---

## 3. Improving the Test Suite or Fixtures

### Fixture generator (`tests/generate_fixtures.py`)

The fixture generator must remain:
- **Deterministic** — same seed, same output, every time, on every platform
- **Self-contained** — no network calls, no external tools beyond Python stdlib +
  Biopython
- **Fast** — target <30 seconds to generate all fixtures on a modern laptop

If you add a new project with automated tests, add a corresponding fixture
generator function and wire it into `main()`.

### Test files

- One test file per project: `tests/test_<project_name>.py`
- Tests must accept `--output-dir` as a pytest option and point at model output
- Tests must be runnable without the model output (skip gracefully if dir not provided)
- Tests should check invariants, not just file existence

### Ground-truth fixture correctness

If you find an error in a ground-truth fixture (wrong SNP distance, wrong AMR
classification, etc.), open an issue before fixing it. A fixture correction
invalidates any runs scored against the old fixture — this needs to be documented.

---

## 4. Reporting Prompt Ambiguities

If you run a project and find the prompt is genuinely ambiguous — a reasonable model
could interpret it two different ways and produce different valid outputs — open an
issue tagged **"prompt ambiguity"**.

Include:
- Which project and prompt version
- What the ambiguity is
- What interpretation you used in your run
- What the alternative interpretation is

We will clarify the prompt in `v1.1` and note the change in `docs/prompt_changelog.md`.

**Important:** do not report "the model got it wrong" as a prompt ambiguity. If the
prompt says "use `cyvcf2`" and the model uses `pysam`, that is a model failure, not
an ambiguous prompt.

---

## 5. Code Style

- Python: PEP 8, type hints on all public functions, `pathlib` for paths
- R: tidyverse style, `<-` assignment
- All new code should include a brief docstring or comment block explaining purpose
- No dependencies beyond those listed in `environments/` or `requirements.txt`

---

## 6. Conduct

This is a scientific benchmark project. Contributions are evaluated on accuracy,
reproducibility, and domain appropriateness — not on which model or harness performs
best. Results that are fabricated, cherry-picked, or scored inconsistently with the
rubric will be rejected.

If you have questions, open an issue. We are happy to help you get a valid run set up.
