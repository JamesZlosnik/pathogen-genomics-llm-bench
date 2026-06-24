# Project 03 — Outbreak Cluster Report
## Canonical Prompt v1.0

> **Instructions for use:** Copy the text below the horizontal rule verbatim into your
> harness. Do not paraphrase, add context, or modify the prompt. If the model enters a
> planning phase, allow it to proceed naturally and record the exchange in `session_log.md`.
> Answer clarifying questions honestly using only information present in this prompt.

---

I have the following files from a bacterial outbreak investigation:

- `data/snp_distance_matrix.csv` — a pairwise SNP distance matrix (samples as row and
  column headers, values are integer SNP distances)
- `data/metadata.csv` — sample metadata with columns: `sample_id`, `collection_date`
  (YYYY-MM-DD), `location` (health authority name), `host` (human/animal/environment),
  `mlst_st` (sequence type as integer or "novel"), `species`
- `data/tree.nwk` — a Newick-format maximum likelihood phylogenetic tree for the same
  samples

Please write an R script called `outbreak_report.R` that produces a self-contained HTML
report using R Markdown (knitted via `rmarkdown::render()`). The report should contain:

1. **Cluster assignment table** — define clusters using single-linkage clustering on the
   SNP distance matrix with a threshold passed as a command-line argument `--threshold`
   (default: 10 SNPs). Output the cluster assignments as a table with columns:
   `sample_id`, `cluster_id`, `mlst_st`, `collection_date`, `location`, `host`.
   Clusters with only one member should be labelled `singleton`.

2. **Minimum spanning tree figure** — constructed from the SNP distance matrix, nodes
   coloured by `location`, node labels showing `sample_id`, edge labels showing SNP
   distance. Use `ggraph` and `tidygraph`. Only show edges that are part of the MST.

3. **Phylogenetic tree figure** — the provided Newick tree with tip labels coloured by
   `location` and an aligned heatmap strip showing `host`. Use `ggtree` and `ggplot2`.

4. **Plain-English summary paragraph** suitable for a public health audience. It should
   state: the number of samples, the SNP threshold used, the number of clusters identified
   (excluding singletons), the largest cluster size, the date range of the investigation,
   and the locations represented.

Use `optparse` for command-line argument parsing with `--threshold`, `--metadata`,
`--matrix`, `--tree`, and `--outdir` arguments. The rendered HTML should be written to
`results/outbreak_report.html`.

Use `tidyverse`, `ggplot2`, `ggtree`, `treeio`, `ggraph`, `tidygraph`, and `rmarkdown`.
Do not use base R graphics. Colour palettes should use `RColorBrewer` or `viridis`.

Input: `data/snp_distance_matrix.csv`, `data/metadata.csv`, `data/tree.nwk`
Output: `results/outbreak_report.html`
