# Project 06 — Phylogenetic Tree + Metadata Visualization
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

I have the following files:

- `data/tree.nwk` — a Newick-format maximum likelihood phylogenetic tree (midpoint-rooted)
- `data/metadata.csv` — sample metadata with columns: `sample_id`, `collection_date`
  (YYYY-MM-DD), `country`, `clade` (categorical, up to 8 levels), `mlst_st` (integer or
  "novel"), `amr_phenotype` (comma-delimited list of resistant drug classes, or "susceptible")

Please write an R script called `phylo_viz.R` that produces a multi-panel figure saved
as both `results/phylo_figure.pdf` (width=14, height=10, units=inches) and
`results/phylo_figure.png` (dpi=300):

**Panel layout:**
1. **Left panel — phylogenetic tree** using `ggtree`:
   - Rectangular layout, midpoint-rooted
   - Tip labels coloured by `clade` using a `RColorBrewer` qualitative palette
   - Node support values shown on internal nodes if present in the tree (as bootstrap or
     UFBoot values), only for nodes with support ≥ 70
   - A time axis or scale bar showing substitutions/site

2. **Middle panel — AMR heatmap** aligned to tree tips using `gheatmap()`:
   - One column per unique drug class parsed from `amr_phenotype`
   - Fill: resistant = solid colour, susceptible = white
   - Use a single accent colour for resistance (e.g. `#d73027`)
   - Column labels rotated 45°

3. **Right panel — collection date strip** aligned to tree tips:
   - A dot plot or segment showing `collection_date` on a continuous time axis
   - Points coloured by `country`

Combine panels using `patchwork` or `aplot`. Use `treeio::read.newick()` for tree import.
Use `ggtree`, `ggplot2`, `dplyr`, `tidyr`, `patchwork` (or `aplot`), and `RColorBrewer`.
Do not use base R graphics.

Use `optparse` with arguments: `--tree`, `--metadata`, `--outdir` (default: `results`).
The script must run non-interactively via `Rscript phylo_viz.R --tree data/tree.nwk
--metadata data/metadata.csv`.

Suppress all package startup messages. The script should exit with a non-zero status
and a clear error message if input files are missing or if the tree tip labels do not
match `sample_id` values in the metadata (after reporting how many matched vs. unmatched).


Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.

Input: `data/tree.nwk`, `data/metadata.csv`
Output: `results/phylo_figure.pdf`, `results/phylo_figure.png`
