# Project 08 — FASTA Parser
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a multi-sequence FASTA file at `data/sequences.fasta` that may be gzipped
(`.fasta.gz`) or plain (`.fasta`). The file contains bacterial genome sequences or
contigs.

Please write a Python script called `fasta_stats.py` that:

1. Reads the input FASTA file using Biopython (`Bio.SeqIO`), handling both gzipped and
   plain input transparently based on the file extension.
2. For each sequence record, computes:
   - Sequence ID (everything before the first space in the header)
   - Full description (the complete header line)
   - Length (bp)
   - GC content (%) — calculated as `(G + C) / (total length - N count) * 100`.
     If a sequence is entirely N, report GC as `NA`.
   - N count (absolute number of N or n bases)
   - N proportion (N count / total length)
3. Writes a per-sequence TSV to `results/sequence_stats.tsv` with columns:
   `seq_id`, `description`, `length_bp`, `gc_pct`, `n_count`, `n_proportion`.
   Round `gc_pct` and `n_proportion` to 4 decimal places.
4. Prints a summary to stdout:
   ```
   Input file:        sequences.fasta
   Total sequences:   XXXX
   Total length (bp): XXXX
   Min length (bp):   XXXX
   Max length (bp):   XXXX
   Mean length (bp):  XXXX
   N50 (bp):          XXXX
   Mean GC (%):       XX.XXXX
   Total N bases:     XXXX
   ```
   N50 is defined as: the sequence length such that sequences of this length or longer
   account for at least 50% of the total assembly length. Compute it correctly from the
   sorted sequence lengths.
5. Optionally filters output to sequences meeting a minimum length threshold via
   `--min_length` (default: 0, i.e. no filtering). Filtered sequences are excluded from
   both the TSV and the summary stats.

Use `argparse` with: `--input` (required), `--outdir` (default: `results`),
`--min_length` (default: 0), `--version` (`1.0.0`). Include `--help`.
Use `pathlib` for paths. Use `logging` at INFO level.

Input: `data/sequences.fasta` (or `data/sequences.fasta.gz`)
Output: `results/sequence_stats.tsv`

Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.
