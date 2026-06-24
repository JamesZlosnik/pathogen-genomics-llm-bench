# How to Run a Benchmark

This document walks you through a complete benchmark run from clone to scored result.
It assumes you have already read `docs/setup_guide.md` and have an inference server
and harness installed and working.

**Time to complete your first run:** 30–90 minutes depending on the project and model.

---

## Overview

A benchmark run has six stages:

```
1. Prepare          Set up fixtures and working directory
2. Choose           Pick a model, harness, provider, and project
3. Run              Deliver the prompt and record the session
4. Test             Run automated correctness tests on the output
5. Score            Complete the rubric and evaluation notes
6. Submit           Add the run to the repo
```

---

## Stage 1: Prepare

### 1a. Clone and install

```bash
git clone https://github.com/BCCDC-PHL/pathogen-genomics-llm-bench
cd pathogen-genomics-llm-bench
pip install pytest pandas numpy biopython cyvcf2
```

### 1b. Generate fixture data

The test suite needs synthetic reference data to validate model outputs against.
Generate it once — you don't need to regenerate unless fixtures change.

```bash
python tests/generate_fixtures.py
```

This produces `tests/fixtures/` with:
- `samples.txt` — 10 sample IDs used across all projects
- `vcf/samples.vcf.gz` — multi-sample VCF with known pairwise SNP distances
- `amrfinder/` — per-sample AMRFinderPlus TSVs
- `fastq/reads.fastq.gz` — synthetic FASTQ with known QC properties
- `assemblies/` — FASTA genome assemblies with known stats
- `mlst/wide_table.tsv` — wide-format MLST table
- `depth/` — samtools depth -a style coverage files
- `expected/` — ground-truth reference outputs for all of the above

> All fixtures are deterministic (seeded). Re-running `generate_fixtures.py` always
> produces identical files. Do not edit fixture files manually.

### 1c. Read the example run

Before running anything, spend 5 minutes reading through the example run:

```
runs/2025-07-15_qwen2.5-coder-14b_opencode_mlx_01/
├── session_log.md   ← read this first
├── evaluation.md
└── output/snp_distance.py
```

This shows you what a complete, well-recorded run looks like — including what the
planning phase and grill questions look like in practice.

---

## Stage 2: Choose

### 2a. Choose a project

If this is your first run, start with **Project 08** (FASTA parser) or **Project 09**
(TSV reformatter) — Tier 1 tasks that any competent model should pass. This lets you
validate your setup before investing time in harder projects.

Read the project brief:
```bash
cat projects/08_fasta_parser/PROMPT.md
```

See `projects/README.md` for the full list and difficulty tiers.

### 2b. Choose a model, harness, and provider

Refer to `docs/setup_guide.md` for installation. For a first run, a sensible default is:

| Component | Recommendation |
|-----------|---------------|
| Model | Qwen2.5-Coder-14B-Instruct Q4_K_M |
| Provider | mlx-lm (Apple Silicon) or llama.cpp (any platform) |
| Harness | OpenCode or Claude Code |

If you are on Apple Silicon with ≥16 GB RAM, mlx-lm + Qwen2.5-Coder-14B is a
good starting point.

### 2c. Decide: PROMPT.md or PROMPT_nogrill.md?

| Use | When |
|-----|------|
| `PROMPT.md` | Standard runs — allows the model to plan and ask questions |
| `PROMPT_nogrill.md` | Single-pass baseline — model must execute without clarification |

Use `PROMPT.md` for most runs. Use `PROMPT_nogrill.md` when comparing a harness that
doesn't support interactive planning, or when you want a controlled single-pass result.

### 2d. Create your run directory

```bash
# Convention: YYYY-MM-DD_<model>_<harness>_<provider>_<project_id>
mkdir -p runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08/output

# Copy the session log template
cp runs/session_log_template.md \
   runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08/session_log.md
```

Fill in the **Run Metadata** table in `session_log.md` before you start (model name,
quantization, harness version, provider version, context window, temperature).
Do this now — it's easy to forget details after the fact.

---

## Stage 3: Run

### 3a. Set up your working directory

The model will write files relative to wherever you launch the harness. Create a
clean working directory for this run and copy in the fixture data the project needs:

```bash
# Example for project 08 (FASTA parser)
cd runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08

mkdir -p data results

# Copy the relevant fixture data
cp ../../tests/fixtures/assemblies/SAMPLE-001.fasta data/sequences.fasta
```

Check the project's `PROMPT.md` for the exact input paths it expects.

### 3b. Place the agent conventions file in your working directory

`CLAUDE.md` and `AGENTS.md` contain identical coding conventions — they exist as two
filenames because different harnesses look for different filenames:

| File | Read by |
|------|---------|
| `CLAUDE.md` | Claude Code (automatic) |
| `AGENTS.md` | OpenCode, Codex CLI, and other OpenAI-spec harnesses (automatic) |

Copy both into your working directory so the conventions are picked up regardless
of which harness you use:

```bash
cp ../../CLAUDE.md .
cp ../../AGENTS.md .
```

> **Why this matters for comparability:** running with and without these files produces
> different outputs. Always use them, and record in your run metadata that you did.

### 3c. Start your inference server

```bash
# mlx-lm example
python -m mlx_lm.server \
  --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit \
  --port 8080 \
  --max-tokens 32768

# Verify it's up
curl -s http://localhost:8080/v1/models | python3 -m json.tool
```

### 3d. Launch the harness and deliver the prompt

Open a new terminal in your run working directory. Launch the harness:

```bash
# OpenCode example
cd runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08
opencode --provider local --model qwen2.5-coder-14b
```

Then paste the prompt from `projects/08_fasta_parser/PROMPT.md` — **verbatim**.
Do not paraphrase or add context.

### 3e. Handle the planning and grill phase

If the model produces a plan before writing code, read it and respond with either
"Accepted" or a brief clarification. If the model asks questions, answer them
**using only information already in the prompt**. Do not volunteer extra context.

Record everything verbatim in `session_log.md` as you go:
- Section 2: the plan the model produced
- Section 3: each question and your answer

> **Key rule:** if the model asks something the prompt genuinely doesn't specify,
> say so explicitly ("The prompt doesn't specify — use your best judgement") and
> record that. Do not invent an answer to make the model succeed.

### 3f. Let the model run

Don't intervene unless the harness crashes or hangs. If the model produces wrong
output, record it and score it — do not re-prompt. A second attempt is a new run
with its own directory.

### 3g. Save the transcript

If your harness produces a session transcript or log file, save it to
`session_log.md` Section 4 or as a separate `transcript.log` in the run directory.

### 3h. Inventory the output

List every file the model produced in Section 5 of `session_log.md`. Note which
files are present and non-empty.

---

## Stage 4: Test

Run the automated test suite against the model's output. This requires the fixture
data to be generated (Stage 1b) and the model's script to have been run against
the fixture input data.

### 4a. Run the model's script against fixture data

```bash
# Example for project 08
cd runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08

python output/fasta_stats.py \
  --input data/sequences.fasta \
  --outdir output/results/
```

If the script crashes or produces no output, record the error in Section 4 of
`session_log.md` and score accordingly — do not debug the script for the model.

### 4b. Run pytest

```bash
# From the repo root
pytest tests/test_snp_matrix.py \
  --output-dir runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08/output/ \
  -v
```

Paste the full pytest output into Section 6 of `session_log.md`.

Not all projects have automated tests yet — check `tests/README.md` for which
projects have corresponding test files. For projects without tests, note this in
your session log and rely on manual inspection of the output.

---

## Stage 5: Score

Open `scoring/rubric.md` and score the run on the five dimensions:

| Dimension | What it measures |
|-----------|----------------|
| Correctness (0–4) | Does the output produce the right answer? |
| Code Quality (0–4) | Is the code readable, idiomatic, well-structured? |
| Domain Appropriateness (0–4) | Does it reflect pathogen genomics knowledge? |
| Completeness (0–4) | Were all requested outputs produced? |
| Autonomous Execution (0–4) | How much human intervention was needed? |

Fill in Section 8 of `session_log.md` and create `evaluation.md` using this template:

```markdown
# Run Evaluation

**Date:**
**Model:**
**Harness:**
**Provider:**
**Project:**

## Scores

| Dimension | Score (0–4) | Notes |
|-----------|------------|-------|
| Correctness | | |
| Code Quality | | |
| Domain Appropriateness | | |
| Completeness | | |
| Autonomous Execution | | |
| **Total** | **/20** | |

## Automated Tests
`X / Y passed (Z%)`

## Notable Strengths

## Notable Issues

## Time to Completion
```

Also add a row to `scoring/scorecard_template.csv`.

### Scoring tips

- **Correctness** should be anchored to the automated test pass rate where tests exist.
  A script that passes all tests scores 4; one that passes none scores 0.
- **Domain Appropriateness** is where hallucinated tool names, wrong AMR categories,
  or incorrect MLST edge case handling should be penalised.
- **Autonomous Execution** is not about whether the model succeeded — it's about how
  much hand-holding was required. A model that failed cleanly and autonomously can still
  score 2 here.
- When in doubt, be conservative. It is better to have consistent slightly-low scores
  than inconsistent scores that vary by evaluator mood.

---

## Stage 6: Submit

If you want to contribute your run to the repo:

```bash
# From the repo root
git checkout -b run/2025-09-01-qwen-opencode-mlx-08
git add runs/2025-09-01_qwen2.5-coder-14b_opencode_mlx_08/
git add scoring/scorecard_template.csv
git commit -m "Add run: qwen2.5-coder-14b / opencode / mlx / project 08"
git push origin run/2025-09-01-qwen-opencode-mlx-08
# Open a pull request
```

See `CONTRIBUTING.md` for the full submission checklist, including what to include
and what to exclude (no patient data, no real sample IDs, no files >10 MB).

---

## Reference: Input Data by Project

| Project | Input files needed | Fixture source |
|---------|-------------------|----------------|
| 01 SNP distance matrix | `data/samples.vcf.gz`, `data/samples.txt` | `tests/fixtures/vcf/`, `tests/fixtures/samples.txt` |
| 02 AMR gene parser | `data/amrfinder/<sample>_amrfinder.tsv`, `data/samples.txt` | `tests/fixtures/amrfinder/`, `tests/fixtures/samples.txt` |
| 03 Outbreak cluster report | `data/snp_distance_matrix.csv`, `data/metadata.csv`, `data/tree.nwk` | `tests/fixtures/expected/snp_distance_matrix.csv` + hand-craft metadata/tree |
| 04 Nextflow QC pipeline | paired FASTQ files | `tests/fixtures/fastq/` (single-end; adapt for paired) |
| 05 MLST batch typer | `data/assemblies/<sample>.fa`, `data/samples.txt` | `tests/fixtures/assemblies/`, `tests/fixtures/samples.txt` |
| 06 Phylo + metadata viz | `data/tree.nwk`, `data/metadata.csv` | hand-craft or use a public toy dataset |
| 07 Sequence QC filter | `data/reads.fastq.gz` | `tests/fixtures/fastq/reads.fastq.gz` |
| 08 FASTA parser | `data/sequences.fasta` | `tests/fixtures/assemblies/SAMPLE-001.fasta` |
| 09 TSV reformatter | `data/wide_table.tsv` | `tests/fixtures/mlst/wide_table.tsv` |
| 10 Assembly stats | `data/assemblies/<sample>.fasta`, `data/samples.txt` | `tests/fixtures/assemblies/`, `tests/fixtures/samples.txt` |
| 11 Coverage depth | `data/depth/<sample>.depth.tsv`, `data/samples.txt` | `tests/fixtures/depth/`, `tests/fixtures/samples.txt` |
| 12 VCF annotation parser | `data/annotated.vcf.gz` | not yet generated — use a public SnpEff-annotated VCF |

> Projects 03, 06, and 12 require input data not yet fully covered by the fixture
> generator. See each project's `PROMPT.md` for input format specifications and
> source a suitable public dataset (e.g. from a published outbreak study or NCBI).

---

## Quick Reference Card

```
git clone ...  →  pip install pytest pandas numpy biopython cyvcf2
                →  python tests/generate_fixtures.py

Pick project   →  read projects/NN_.../PROMPT.md
               →  mkdir -p runs/DATE_model_harness_provider_NN/output
               →  cp runs/session_log_template.md runs/.../session_log.md
               →  fill in metadata table NOW

Set up run dir →  mkdir data results
               →  cp tests/fixtures/... data/
               →  cp CLAUDE.md . && cp AGENTS.md .

Start server   →  python -m mlx_lm.server --model ... --max-tokens 32768
               →  curl localhost:8080/v1/models  ← verify

Run harness    →  paste PROMPT.md verbatim
               →  record plan + grill in session_log.md sections 2–3
               →  do not re-prompt on failure

Test output    →  python output/<script>.py --input data/... --outdir output/results/
               →  pytest tests/test_X.py --output-dir runs/.../output/ -v
               →  paste pytest output into session_log.md section 6

Score          →  read scoring/rubric.md
               →  fill session_log.md section 8
               →  write evaluation.md
               →  add row to scoring/scorecard_template.csv

Submit         →  git add runs/...  →  PR
```
