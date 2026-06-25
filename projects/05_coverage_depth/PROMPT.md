# Project 11 — Coverage Depth Summariser
## Canonical Prompt v1.0

> **Instructions for use:** Copy the text below the horizontal rule verbatim into your
> harness. Do not paraphrase, add context, or modify the prompt. If the model enters a
> planning phase, allow it to proceed naturally and record the exchange in `session_log.md`.
> Answer clarifying questions honestly using only information present in this prompt.

---

I have per-base depth files produced by `samtools depth -a` for a batch of samples.
Each file is at `data/depth/<sample_id>.depth.tsv` and has three tab-delimited columns
with no header: `contig`, `position`, `depth`. The `-a` flag means all positions are
reported, including those with zero depth. A list of sample IDs is at `data/samples.txt`.

Please write a Python script called `summarise_depth.py` that:

1. For each sample, reads the depth file and computes:
   - **Genome-wide statistics** (across all positions):
     - `mean_depth` — mean depth across all positions (including zeros)
     - `median_depth` — median depth
     - `min_depth` — minimum depth
     - `max_depth` — maximum depth
     - `pct_covered_1x` — percentage of positions with depth ≥ 1
     - `pct_covered_10x` — percentage of positions with depth ≥ 10
     - `pct_covered_20x` — percentage of positions with depth ≥ 20
     - `pct_covered_100x` — percentage of positions with depth ≥ 100
     - `total_positions` — total number of positions in the depth file
   - **Per-contig statistics** — for each contig, the same set of metrics above
     plus `contig` name and `contig_length` (number of positions reported for that
     contig in the depth file).
   - Flag `low_coverage` (1/0) at genome level: 1 if `pct_covered_10x` < 90.0.

2. Writes genome-wide summary to `results/depth_summary.tsv` — one row per sample,
   columns: `sample_id`, `mean_depth`, `median_depth`, `min_depth`, `max_depth`,
   `pct_covered_1x`, `pct_covered_10x`, `pct_covered_20x`, `pct_covered_100x`,
   `total_positions`, `low_coverage`.

3. Writes per-contig summary to `results/depth_per_contig.tsv` — columns:
   `sample_id`, `contig`, `contig_length`, `mean_depth`, `median_depth`,
   `pct_covered_1x`, `pct_covered_10x`, `low_coverage`.

4. Prints to stdout:
   ```
   Samples processed:           XX
   Samples with low coverage:   XX
   Mean genome-wide depth:      XX.XX
   ```

5. Handles large depth files efficiently. Do not load the entire file into memory at
   once — process contig blocks iteratively. Files may have millions of rows.

6. Exits with a non-zero status and a logged error if a sample's depth file is missing.

Use `argparse` with: `--depth_dir` (default: `data/depth`), `--samples`
(default: `data/samples.txt`), `--outdir` (default: `results`),
`--low_cov_threshold` (default: 90.0, the pct_covered_10x threshold below which a
sample is flagged), `--version` (`1.0.0`). Include `--help`.
Use `pandas` for output table construction. Use `numpy` for per-block statistics.
Use `pathlib`. Use `logging` at INFO level (DEBUG with `--verbose`).

Input: `data/depth/<sample_id>.depth.tsv`, `data/samples.txt`
Output: `results/depth_summary.tsv`, `results/depth_per_contig.tsv`
