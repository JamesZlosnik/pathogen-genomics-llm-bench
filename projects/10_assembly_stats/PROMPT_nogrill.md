# Project 10 — Genome Assembly Statistics
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a directory of bacterial genome assemblies in FASTA format at `data/assemblies/`,
named `<sample_id>.fasta`. Assemblies may have multiple contigs. A list of sample IDs
is at `data/samples.txt` (one per line).

Please write a Python script called `assembly_stats.py` that:

1. For each assembly, computes the following statistics considering only contigs that
   meet a minimum length threshold (`--min_contig_length`, default: 500 bp). Contigs
   below this threshold are excluded from all calculations.
2. Per-assembly statistics:
   - `sample_id`
   - `total_contigs` — number of contigs in the raw assembly (before length filtering)
   - `filtered_contigs` — number of contigs after applying `--min_contig_length`
   - `total_length_bp` — sum of filtered contig lengths
   - `largest_contig_bp` — length of the longest filtered contig
   - `n50_bp` — N50 computed from filtered contigs. Definition: sort contigs by length
     descending; N50 is the length of the contig at which the cumulative sum of lengths
     reaches or exceeds 50% of the total assembly length.
   - `n90_bp` — same as N50 but at 90% of total length
   - `l50` — the number of contigs whose cumulative length reaches N50 (i.e. the count
     of contigs in the N50 set)
   - `gc_pct` — GC% across all filtered contigs combined, excluding N bases from the
     denominator
   - `n_count` — total N bases across all filtered contigs
   - `n_proportion` — N bases / total filtered length
3. Writes per-assembly stats to `results/assembly_stats.tsv` (one row per sample).
4. Writes a run-level summary to stdout:
   ```
   Samples processed:      XX
   Mean total length (bp): XXXXXXX
   Mean N50 (bp):          XXXXXXX
   Mean GC (%):            XX.XX
   Samples with N50 < 50000: XX
   ```
5. Exits with a non-zero status and logs an error if any sample in `samples.txt` has
   no corresponding FASTA file.

Use `argparse` with: `--assemblies` (default: `data/assemblies`), `--samples`
(default: `data/samples.txt`), `--outdir` (default: `results`),
`--min_contig_length` (default: 500), `--version` (`1.0.0`). Include `--help`.
Use `Biopython` for FASTA parsing. Use `pandas` for output. Use `pathlib`.
Use `logging` at INFO level (DEBUG with `--verbose`).
Do not use any external assembly QC tools (e.g. QUAST) — compute all statistics
directly in Python.

Input: `data/assemblies/<sample_id>.fasta`, `data/samples.txt`
Output: `results/assembly_stats.tsv`

Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.
