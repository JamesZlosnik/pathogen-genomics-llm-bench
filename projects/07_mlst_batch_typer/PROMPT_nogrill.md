# Project 05 — MLST Batch Typer
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a directory of bacterial genome assemblies in FASTA format at `data/assemblies/`,
named `<sample_id>.fa`. A list of sample IDs is at `data/samples.txt` (one per line).
The `mlst` tool (Torsten Seemann's PubMLST tool) is installed and available on `$PATH`.

Please write a Python script called `run_mlst.py` that:

1. Runs `mlst` on each assembly file. Use `--quiet` to suppress progress output.
   Do not specify a scheme — allow `mlst` to autodetect.
2. Captures stdout from `mlst` (tab-delimited: `FILE`, `SCHEME`, `ST`, then one column
   per allele locus).
3. Parses the output into a tidy pandas DataFrame and saves it to
   `results/mlst_summary.tsv` with columns: `sample_id`, `scheme`, `st`, and one column
   per allele locus named as the locus (e.g. `adk`, `fumC`, etc.).
4. Handles the following edge cases without crashing:
   - Novel alleles — `mlst` reports these as `~<allele>` (new allele variant) or with
     a `?` suffix. Preserve the raw value in the output.
   - Novel STs — reported as `-`. Preserve as `-` in the `st` column.
   - Missing loci — reported as `-`. Preserve as `-`.
   - Samples where `mlst` exits non-zero or produces no output — record `scheme` as
     `FAILED`, `st` as `FAILED`, alleles as empty, and log a warning.
   - Samples with multiple scheme matches — keep all rows, add a note in a
     `notes` column.
5. Prints to stdout: total samples, samples successfully typed, samples with novel ST,
   samples that failed, and the distribution of schemes detected.
6. Runs samples in parallel using `concurrent.futures.ThreadPoolExecutor`. Accept
   `--threads` argument (default: 4).

Use `argparse` with: `--assemblies` (default: `data/assemblies`), `--samples`
(default: `data/samples.txt`), `--outdir` (default: `results`), `--threads` (default: 4),
`--version` (`1.0.0`).

Use `logging` (INFO level by default, DEBUG with `--verbose`). Use `pathlib` for paths.
Do not use shell=True in subprocess calls.


Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.

Input: `data/assemblies/<sample_id>.fa`, `data/samples.txt`
Output: `results/mlst_summary.tsv`
