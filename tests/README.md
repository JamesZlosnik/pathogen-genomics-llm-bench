# Automated Tests

Pytest-based tests that verify model outputs against known-correct reference data. Run these after each evaluation to get an objective correctness score.

## Setup

```bash
pip install pytest pandas biopython
```

## Running Tests

```bash
# Test a specific run's output
pytest tests/ --output-dir runs/2025-07-01_gemma4-27b_opencode_mlx_01/output/ -v

# Run all tests for a project
pytest tests/test_snp_matrix.py -v
```

## Test Strategy

Each test module maps to a project. Tests check:

- **Structural correctness** — right file format, right columns, right number of rows
- **Numerical correctness** — distances/values within tolerance of reference
- **Edge case handling** — missing data, novel STs, zero-distance self-comparisons
- **Domain-specific invariants** — e.g. SNP matrix must be symmetric; self-distance = 0

## Fixtures

Reference inputs and expected outputs live in `fixtures/`. These are either:
- Synthetic datasets with known ground truth (preferred — avoids data sharing issues)
- Anonymised/subsampled real data where synthetic is impractical

```
fixtures/
├── sample_vcf/              # Small multi-sample VCF for SNP distance tests
├── sample_resfinder/        # Example ResFinder TSV outputs
├── sample_fastq/            # Tiny FASTQ for QC filter tests
├── sample_assemblies/       # Small FASTA files for MLST tests
├── sample_tree/             # Newick tree + metadata CSV
└── expected_outputs/        # Ground truth for each project
    ├── snp_matrix.csv
    ├── amr_summary.tsv
    └── qc_filter_summary.txt
```

## Key Invariants to Test (by project)

### Project 01 — SNP Distance Matrix
- Matrix is square and symmetric
- Diagonal is all zeros
- Values are non-negative integers
- Flagged pairs all have distance ≤ threshold
- No samples dropped

### Project 02 — AMR Gene Parser
- One row per sample, no duplicates
- Gene class columns sum correctly
- Carbapenemase flag is correct
- Handles samples with no hits (all zeros)

### Project 03 — Outbreak Cluster Report
- HTML file is valid and opens
- Cluster assignments match manual inspection for known test case
- Summary paragraph contains cluster count and SNP threshold

### Project 04 — Nextflow Pipeline
- `nextflow run main.nf --help` exits cleanly
- DSL2 syntax check passes (`nextflow lint`)
- Pipeline runs to completion on toy data
- MultiQC output present

### Project 05 — MLST Batch Typer
- One row per input assembly
- Novel ST samples show "-" not an error
- All allele columns present for the scheme

### Project 06 — Phylo Viz
- R script runs without error
- Output figure file exists and is non-empty
- Tip labels match input tree

### Project 07 — QC Filter
- Total reads = passing + failing
- All passing reads meet all thresholds
- Summary TSV has correct column names
- No reads written to wrong file
