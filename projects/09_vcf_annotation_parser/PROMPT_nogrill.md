# Project 12 — VCF Annotation Parser (SnpEff)
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have a SnpEff-annotated VCF file at `data/annotated.vcf.gz`. SnpEff writes functional
annotations into the `ANN` field of the INFO column. Each variant may have multiple `ANN`
entries (one per transcript), pipe-delimited, in the following order:

`Allele | Annotation | Annotation_Impact | Gene_Name | Gene_ID | Feature_Type |
Feature_ID | Transcript_BioType | Rank | HGVS.c | HGVS.p | cDNA_pos/cDNA_len |
CDS_pos/CDS_len | AA_pos/AA_len | Distance | ERRORS/WARNINGS/INFO`

Please write a Python script called `parse_snpeff.py` that:

1. Parses `data/annotated.vcf.gz` using `cyvcf2`. For each variant, extracts:
   - `chrom`, `pos` (1-based), `ref`, `alt` (first ALT allele only)
   - `filter` — FILTER field value (PASS or the filter name); if multiple, join with `;`
   - From the `ANN` field — for each annotation entry:
     - `allele`, `annotation` (effect), `impact` (HIGH/MODERATE/LOW/MODIFIER),
       `gene_name`, `gene_id`, `feature_type`, `feature_id`, `hgvs_c`, `hgvs_p`
   - When a variant has multiple ANN entries (multiple transcripts), keep all of them
     as separate rows in the output.

2. Writes a flat TSV to `results/snpeff_annotations.tsv` with one row per
   variant-annotation pair and columns:
   `chrom`, `pos`, `ref`, `alt`, `filter`, `annotation`, `impact`, `gene_name`,
   `gene_id`, `feature_type`, `feature_id`, `hgvs_c`, `hgvs_p`.

3. Writes a per-gene impact summary to `results/gene_impact_summary.tsv` with columns:
   `gene_name`, `high_impact`, `moderate_impact`, `low_impact`, `modifier_impact`,
   `total_variants`. Count distinct `chrom`+`pos`+`ref`+`alt` combinations per gene
   per impact level (not annotation rows, to avoid double-counting multi-transcript hits).

4. Filters to PASS variants only by default. Accept `--include_filtered` flag to
   include all variants regardless of FILTER status.

5. Prints to stdout:
   ```
   Total variants parsed:      XXXX
   PASS variants:              XXXX
   Variants with ANN field:    XXXX
   Variants missing ANN:       XXXX
   Unique genes annotated:     XXXX
   HIGH impact variants:       XXXX
   MODERATE impact variants:   XXXX
   ```

6. Handles variants where the `ANN` field is absent or empty — these should appear in
   the TSV with annotation columns set to `.` (missing) and be counted separately.

Use `argparse` with: `--input` (required), `--outdir` (default: `results`),
`--include_filtered` (flag, default: False), `--version` (`1.0.0`). Include `--help`.
Use `cyvcf2` for VCF parsing. Use `pandas` for output tables. Use `pathlib`.
Use `logging` at INFO level.

Input: `data/annotated.vcf.gz`
Output: `results/snpeff_annotations.tsv`, `results/gene_impact_summary.tsv`

Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.
