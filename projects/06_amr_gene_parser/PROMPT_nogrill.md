# Project 02 — AMR Gene Parser
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a batch of samples that have been run through AMRFinderPlus. For each sample there
is a TSV output file in `data/amrfinder/` named `<sample_id>_amrfinder.tsv`. The sample
IDs are listed in `data/samples.txt` (one per line). The AMRFinderPlus output uses the
standard column headers produced by `amrfinder --plus`.

Please write a Python script called `parse_amr.py` that:

1. Reads each sample's AMRFinderPlus TSV from `data/amrfinder/`.
2. Produces a tidy summary table saved to `results/amr_summary.tsv` with:
   - One row per sample
   - A `sample_id` column
   - One column per AMR gene class (use the `Class` field from AMRFinderPlus output).
     Each class column contains a semicolon-delimited list of the specific gene names
     (`Gene symbol` field) detected in that class, or is empty if none detected.
   - A boolean `carbapenemase_detected` column (1/0) that is 1 if any gene in the
     `Subclass` field equals `CARBAPENEM`.
   - A `total_amr_genes` column with the count of all AMR genes detected per sample.
3. Produces a second long-format table saved to `results/amr_long.tsv` with columns:
   `sample_id`, `gene_symbol`, `class`, `subclass`, `sequence_name`, `scope`,
   `element_type`, `element_subtype`, `method`, `identity_pct`, `coverage_pct`.
   Include only rows where `Element type` is `AMR`. One row per gene per sample.
4. Prints to stdout: total samples processed, total unique AMR gene symbols detected
   across all samples, number of samples with carbapenemase genes.
5. Handles samples with no AMR genes detected (empty or header-only TSV) without
   crashing — these should appear in the summary with all gene class columns empty
   and `total_amr_genes` = 0.

Use `pandas` for all data manipulation. Use `pathlib` for file paths. Use `argparse`
with `--input_dir` (default: `data/amrfinder`), `--samples` (default: `data/samples.txt`),
`--outdir` (default: `results`), and `--version` (`1.0.0`) arguments.

Log progress using Python's `logging` module at INFO level.


Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.

Input: `data/amrfinder/<sample_id>_amrfinder.tsv` for each sample, `data/samples.txt`
Output: `results/amr_summary.tsv`, `results/amr_long.tsv`
