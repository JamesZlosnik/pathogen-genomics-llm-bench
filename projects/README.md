# Evaluation Projects

Each project is a self-contained benchmarking task. The goal is to test a model+harness
combination on a realistic pathogen genomics coding task while keeping conditions as
reproducible as possible across runs and across models.

Projects are numbered in order of difficulty — 01 is the easiest, 12 is the hardest.

---

## Prompt Protocol

Every project contains two prompt files:

| File | Purpose |
|------|---------|
| `PROMPT.md` | Canonical prompt — use for all standard runs. Allows the model to plan and ask clarifying questions naturally. |
| `PROMPT_nogrill.md` | No-plan variant — identical task but instructs the model to skip clarification and execute directly. Use for single-pass baseline comparisons. |

### Rules for prompt delivery
1. **Copy the prompt verbatim.** Do not paraphrase, add context, or "help" the model
   with extra information.
2. **Answer clarifying questions honestly** using only information already present in
   the prompt. Do not volunteer information that isn't there. If the model asks something
   the prompt genuinely doesn't specify, say so and let the model decide.
3. **Record everything** in `session_log.md` (see `runs/session_log_template.md`).
   The plan, every question, every answer, and the full harness transcript are primary
   benchmark data.
4. **Do not re-prompt** if the model produces wrong output. Record what happened and
   score it. A second attempt is a separate run with a new run directory.

### Plan and grill-me interactions
The plan/grill phase is **not controlled** — it varies naturally by model. This is
intentional: how a model plans and what it asks before coding is diagnostic signal,
not noise. Record it faithfully. When aggregating results, plan quality is captured
in the **Domain Appropriateness** and **Autonomous Execution** rubric dimensions.

If your harness does not support an interactive planning phase (e.g. single-shot API
call), use `PROMPT_nogrill.md` and note this in the run metadata.

---

## Project List — Ordered by Difficulty

Projects are binned into four tiers. Numbers reflect difficulty order — start at 01.

### Tier 1 — Floor (any competent model should pass)
These establish a baseline. Failure here is a strong signal the model is not viable.

| ID | Name | Language | Key Skills Tested |
|----|------|----------|-------------------|
| 01 | FASTA Parser | Python | Biopython, GC% calculation, N50 definition, gzip handling, argparse |
| 02 | TSV/CSV Reformatter | Python | pandas wide-to-long, dynamic column detection, allele status categorisation |

### Tier 2 — Core (domain-competent models should pass)
Standard bioinformatics tasks. Failure usually indicates shallow domain knowledge
or weak handling of edge cases.

| ID | Name | Language | Key Skills Tested |
|----|------|----------|-------------------|
| 03 | Sequence QC Filter | Python | Biopython, per-read stats, multi-filter logic, fail reason reporting |
| 04 | Assembly Stats | Python | Correct N50/N90/L50 definitions, contig filtering, batch processing |
| 05 | Coverage Depth Summariser | Python | samtools depth format, iterative large-file processing, pct coverage thresholds |
| 06 | AMR Gene Parser | Python | AMRFinderPlus TSV format, gene class aggregation, carbapenemase flagging |
| 07 | MLST Batch Typer | Python | subprocess, parallel execution, novel ST / missing allele edge cases |

### Tier 3 — Advanced (requires strong domain + language knowledge)
Multi-step or format-specific tasks where hallucination is easy and verification
is non-trivial.

| ID | Name | Language | Key Skills Tested |
|----|------|----------|-------------------|
| 08 | SNP Distance Matrix | Python | cyvcf2, missing genotype handling, symmetric matrix, transmission pair flagging |
| 09 | VCF Annotation Parser | Python | SnpEff ANN field format, multi-transcript deduplication, impact categorisation |
| 10 | Phylo + Metadata Viz | R | ggtree, gheatmap, patchwork, metadata alignment, publication figure quality |

### Tier 4 — Expert (integration + pipeline correctness)
Failures are expected for most local models. Partial credit is meaningful.

| ID | Name | Language | Key Skills Tested |
|----|------|----------|-------------------|
| 11 | Outbreak Cluster Report | R | ggtree, ggraph, MST, single-linkage clustering, plain-English summary |
| 12 | Nextflow QC Pipeline | Nextflow DSL2 | DSL2 syntax, named emits, dual input modes, conda profiles, provenance |

---

## Difficulty at a Glance

```
TIER 1 (Floor)   TIER 2 (Core)                  TIER 3 (Advanced)     TIER 4 (Expert)
|                |                               |                     |
01  02           03  04  05  06  07              08  09  10            11  12
|                |                               |                     |
FASTA  TSV       QC  N50  Depth  AMR  MLST       SNP  SnpEff  Phylo    Cluster  NF
```

A model that clears Tier 1 and 2 cleanly is viable for day-to-day scripting tasks.
A model that clears Tier 3 is suitable for independent pipeline development work.
Tier 4 is the ceiling — partial credit (e.g. syntactically valid but logically wrong
DSL2) is still informative.

---

## Adding a New Project

1. Create a numbered folder: `NN_short_name/` — assign the number based on difficulty
   relative to existing projects, keeping tiers contiguous
2. Write `PROMPT.md` following the template used in existing projects:
   - Header with project name and prompt version
   - Instructions block (quoted)
   - Horizontal rule
   - The actual prompt
   - Explicit `Input:` / `Output:` section at the end
3. Write `PROMPT_nogrill.md` — identical but with the no-clarification paragraph appended
4. Add `expected_outputs/` with reference files for automated testing if feasible
5. Add test cases to `../tests/` referencing the fixture data
6. Update this README — assign the project to a difficulty tier with justification
7. Bump the prompt version if you ever edit a prompt (`v1.0` -> `v1.1`); never edit
   a versioned prompt retroactively — add a new version so old runs remain reproducible
