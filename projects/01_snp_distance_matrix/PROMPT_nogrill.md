# Project 01 — SNP Distance Matrix
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase (e.g. direct execution mode, or when you want a single-pass
> baseline). The task is identical to `PROMPT.md` but the final paragraph instructs the
> model to proceed without asking questions.

---

I have a directory of paired-end Illumina whole-genome sequencing samples from a bacterial
outbreak investigation. Each sample has already been processed through a variant-calling
pipeline and I have a multi-sample VCF file at `data/samples.vcf.gz` containing SNP calls
for all samples relative to a reference genome. I also have a sample list at
`data/samples.txt` (one sample ID per line).

Please write a Python script called `snp_distance.py` that:

1. Parses `data/samples.vcf.gz` and extracts biallelic SNP positions for each sample,
   ignoring indels and any site where the FILTER field is not PASS.
2. Computes a pairwise SNP distance matrix across all samples. A SNP is counted in the
   distance between two samples only if both samples have a called (non-missing) genotype
   at that site and the genotypes differ.
3. Writes the full pairwise matrix to `results/snp_distance_matrix.csv` (samples as both
   row and column headers).
4. Writes a lower-triangle plain-text table to `results/snp_distance_matrix.txt` in the
   style used by the `snp-dists` tool.
5. Accepts a `--threshold` argument (default: 10) and writes a second CSV to
   `results/putative_transmission_pairs.csv` listing all sample pairs with a SNP distance
   at or below that threshold. Columns: `sample_a`, `sample_b`, `snp_distance`.
6. Prints a brief summary to stdout: total samples, total pairwise comparisons, number of
   pairs below threshold.

Use `cyvcf2` for VCF parsing. Use `pandas` for the matrix and output. Include a `--help`
flag and a `--version` flag (version: `1.0.0`). Handle missing genotypes explicitly —
do not treat missing as reference.

Input: `data/samples.vcf.gz`, `data/samples.txt`
Output: `results/snp_distance_matrix.csv`, `results/snp_distance_matrix.txt`,
        `results/putative_transmission_pairs.csv`

Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.
