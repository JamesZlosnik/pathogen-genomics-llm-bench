# Project 07 — Sequence QC Filter
## Canonical Prompt v1.0

> **Instructions for use:** Copy the text below the horizontal rule verbatim into your
> harness. Do not paraphrase, add context, or modify the prompt. If the model enters a
> planning phase, allow it to proceed naturally and record the exchange in `session_log.md`.
> Answer clarifying questions honestly using only information present in this prompt.

---

I have a gzip-compressed FASTQ file at `data/reads.fastq.gz` containing single-end
Illumina reads (the script should also handle uncompressed `.fastq`). I need a Python
script called `qc_filter.py` that filters reads by quality thresholds and reports
per-read statistics.

The script must:

1. Read the input FASTQ (gzipped or plain) using **Biopython** (`Bio.SeqIO`).
2. For each read, compute:
   - Read length (bp)
   - Mean Phred quality score (averaged across all base quality scores)
   - Proportion of N bases (`N_proportion` = count of 'N' / read length)
3. Apply all three filters:
   - `--min_length` (default: 50) — discard reads shorter than this
   - `--min_mean_qual` (default: 20.0) — discard reads with mean Phred quality below this
   - `--max_n_proportion` (default: 0.05) — discard reads with N proportion above this
   A read must pass **all three** filters to be written to the passing output.
4. Write passing reads to `results/<input_stem>_pass.fastq.gz` (gzipped).
5. Write failing reads to `results/<input_stem>_fail.fastq.gz` (gzipped).
6. Write a per-read TSV to `results/<input_stem>_read_stats.tsv` with columns:
   `read_id`, `length`, `mean_qual`, `n_proportion`, `pass_fail`, `fail_reason`.
   `fail_reason` should be a semicolon-delimited list of which filters failed
   (e.g. `min_length;min_mean_qual`), or empty if the read passed.
7. Print a summary to stdout:
   ```
   Total reads:        XXXXX
   Reads passing:      XXXXX (XX.X%)
   Reads failing:      XXXXX (XX.X%)
     Failed min_length:      XXXXX
     Failed min_mean_qual:   XXXXX
     Failed max_n_proportion: XXXXX
     Failed multiple filters: XXXXX
   ```
   Note: reads failing multiple filters are counted once in the total failing and
   once per individual filter category.

Use `argparse` with: `--input` (required), `--outdir` (default: `results`),
`--min_length`, `--min_mean_qual`, `--max_n_proportion`, `--version` (`1.0.0`).

Use `logging` (INFO level). Use `pathlib`. Do not use `subprocess` — read and write
gzip directly with Python's `gzip` module alongside Biopython. Phred quality scores
are already decoded by Biopython's `SeqIO.parse` with `format="fastq"` — do not
decode manually.

Input: `data/reads.fastq.gz`
Output: `results/reads_pass.fastq.gz`, `results/reads_fail.fastq.gz`,
        `results/reads_read_stats.tsv`
