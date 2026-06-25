# Project 09 — TSV/CSV Reformatter
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a wide-format tabular file at `data/wide_table.tsv` that contains MLST-style
results. It has a variable number of columns depending on the scheme: a `sample_id`
column, a `scheme` column, an `st` column, and then one column per allele locus
(e.g. `adk`, `fumC`, `gyrB`, `icd`, `mdh`, `purA`, `recA` for E. coli Achtman MLST,
but the locus names and count vary and are not fixed). Values may be integers (allele
numbers), `-` (missing/not found), `~<integer>` (novel allele variant), or
`<integer>?` (uncertain call).

Please write a Python script called `reformat_table.py` that:

1. Reads `data/wide_table.tsv` (tab-delimited). Detects the delimiter automatically
   (tab or comma) based on the file extension: `.tsv` → tab, `.csv` → comma.
2. Identifies the allele locus columns automatically as all columns that are not
   `sample_id`, `scheme`, or `st`.
3. Reshapes the table from wide to long format producing a DataFrame with columns:
   `sample_id`, `scheme`, `st`, `locus`, `allele`.
4. Adds a `allele_status` column categorising each allele value:
   - `integer` — a plain integer allele number (e.g. `4`, `12`)
   - `novel` — starts with `~` (e.g. `~342`)
   - `uncertain` — ends with `?` (e.g. `14?`)
   - `missing` — value is `-`
   - `other` — anything else
5. Writes the long-format table to `results/long_table.tsv` (tab-delimited).
6. Writes a per-sample summary to `results/sample_summary.tsv` with columns:
   `sample_id`, `scheme`, `st`, `total_loci`, `missing_loci`, `novel_loci`,
   `uncertain_loci`, `complete` (boolean 1/0: 1 if no missing or novel loci).
7. Prints to stdout: total samples, total loci detected, samples with complete profiles,
   samples with any novel allele, samples with any missing allele.

Use `argparse` with: `--input` (required), `--outdir` (default: `results`),
`--version` (`1.0.0`). Include `--help`.
Use `pandas` for all reshaping. Use `pathlib`. Use `logging` at INFO level.
Do not hardcode locus names. The script must work with any wide-format MLST-style table
regardless of which scheme or how many loci are present.

Input: `data/wide_table.tsv`
Output: `results/long_table.tsv`, `results/sample_summary.tsv`

Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.
