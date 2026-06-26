# Prompt Changelog

This file records every change to a project prompt. Prompts are versioned so that
runs can always be traced back to the exact task specification they used.

**Rule:** never edit a prompt that has been used in a submitted run. Create a new
version instead and record the change here. Old versions are never deleted.

Format: `## Project NN — Name` → `### vX.Y (YYYY-MM-DD)` → what changed and why.

---

## Project 01 — FASTA Parser

### v1.0 (2025-07-01)
Initial release. Specifies Biopython, gzip handling, GC% excluding N bases,
N50 definition, `--min_length` filter, argparse with `--version`.

---

## Project 02 — TSV/CSV Reformatter

### v1.0 (2025-07-01)
Initial release. Specifies dynamic locus column detection, allele status
categorisation (`integer`, `novel`, `uncertain`, `missing`, `other`),
wide-to-long reshape, per-sample summary.

---

## Project 03 — Sequence QC Filter

### v1.0 (2025-07-01)
Initial release. Specifies Biopython, three filters (length, mean Q, N proportion),
per-read TSV with `fail_reason`, gzip I/O via Python `gzip` module.

---

## Project 04 — Assembly Stats

### v1.0 (2025-07-01)
Initial release. Specifies N50/N90/L50 definitions explicitly, 500 bp contig
length filter, `--min_contig_length` parameter, no external tools (e.g. QUAST).

---

## Project 05 — Coverage Depth Summariser

### v1.0 (2025-07-01)
Initial release. Specifies `samtools depth -a` format (no header, three columns),
iterative per-contig processing for large files, pct_covered thresholds at
1x/10x/20x/100x, `--low_cov_threshold` parameter.

---

## Project 06 — AMR Gene Parser

### v1.0 (2025-07-01)
Initial release. Specifies AMRFinderPlus `--plus` output format, wide summary
table with gene class columns, long table with one row per gene, carbapenemase
flag based on `Subclass` field value `CARBAPENEM`.

---

## Project 07 — MLST Batch Typer

### v1.0 (2025-07-01)
Initial release. Specifies `mlst` (Torsten Seemann) tool, `--quiet` flag,
`concurrent.futures.ThreadPoolExecutor` for parallelism, novel allele (`~`)
and uncertain (`?`) handling, `shell=False` requirement.

---

## Project 08 — SNP Distance Matrix

### v1.0 (2025-07-01)
Initial release. Specifies `cyvcf2` for VCF parsing, PASS filter, biallelic
SNPs only, missing genotype handling (not treated as ref), `--threshold` for
transmission pair flagging, snp-dists lower-triangle output format.

---

## Project 09 — VCF Annotation Parser (SnpEff)

### v1.0 (2025-07-01)
Initial release. Specifies SnpEff `ANN` field pipe-delimited format with field
order, multi-transcript rows (one row per ANN entry), per-gene impact summary
with deduplication by distinct variant (not annotation row count),
`--include_filtered` flag.

---

## Project 10 — Phylogenetic Tree + Metadata Visualization

### v1.0 (2025-07-01)
Initial release. Specifies `ggtree` rectangular layout, `gheatmap()` for AMR
heatmap, `aplot` or `patchwork` for panel combination, `treeio::read.newick()`
for import, `RColorBrewer` palettes, `optparse` CLI, non-zero exit on tip label
mismatch.

---

## Project 11 — Outbreak Cluster Report

### v1.0 (2025-07-01)
Initial release. Specifies single-linkage clustering on SNP distance matrix,
`ggraph` + `tidygraph` for MST, `ggtree` for phylogenetic tree, plain-English
summary paragraph, R Markdown rendered via `rmarkdown::render()`, `optparse` CLI.

---

## Project 12 — Nextflow QC Pipeline

### v1.0 (2025-07-01)
Initial release. Specifies DSL2, four processes (FASTQC_RAW, FASTP,
FASTQC_TRIMMED, MULTIQC), dual input modes (directory + samplesheet CSV),
named `emit:` outputs, `conda` and `singularity` profiles, shared conda cache
via `params.cache`, `--help` flag, scripts >5 lines in `bin/`.

---

## How to add a new version

1. Edit the prompt file: copy the existing `PROMPT.md` to `PROMPT_v1_0.md`
   (archive the old version), then edit `PROMPT.md` with the new content
2. Update the header line in `PROMPT.md`: `## Canonical Prompt v1.1`
3. Do the same for `PROMPT_nogrill.md`
4. Add an entry here under the relevant project heading:
   ```
   ### v1.1 (YYYY-MM-DD)
   What changed: <description>
   Why: <reason — e.g. prompt ambiguity reported in issue #XX>
   Affects runs: any run using v1.0 is not directly comparable to v1.1 runs
   ```
5. Open a GitHub issue tagged `prompt-version` linking to this entry
