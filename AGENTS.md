# AGENTS.md — Coding Conventions for this Repository

> **Note:** This file is read automatically by **OpenCode, Codex CLI**, and other
> harnesses that follow the OpenAI agents spec. An identical copy exists as `CLAUDE.md`
> for Claude Code. If you edit one, edit the other. `CLAUDE.md` is the source of truth.


This file describes the coding conventions, patterns, and domain knowledge expected of any AI agent
working in this repository. It is derived from the established practices of the
[BCCDC-PHL](https://github.com/BCCDC-PHL) (BC Centre for Disease Control Public Health Laboratory)
bioinformatics team.

Agents should read this file before writing any code, editing any pipeline, or proposing any
structural changes. Conformance to these conventions is part of the evaluation rubric.

---

## 1. General Principles

- **Reproducibility above all.** Every result must be traceable to a specific tool version,
  database version, and input file checksum. Hard-coding tool versions and emitting provenance
  records is not optional.
- **Public health context.** Outputs from these tools inform clinical and public health decisions.
  Prefer conservative defaults, explicit error handling, and informative failure messages over
  silent failures or permissive assumptions.
- **Tidy data.** Outputs should be in long/tidy format wherever possible. One row per observation.
  Avoid wide matrices as primary outputs unless the downstream tool explicitly requires them.
- **Portability.** Code should run on Linux. Do not assume macOS-specific tools or paths.
  Package management is via **conda/mamba**; do not use pip as the primary dependency manager
  for pipeline environments.

---

## 2. Python

### Style
- Follow **PEP 8**. Use 4-space indentation. Maximum line length 120 characters.
- Use **type hints** on all function signatures.
- Use **docstrings** (Google style) on all public functions and modules.
- Prefer **`argparse`** for CLI tools. Always include `--version` and `--help`.
- Scripts intended to be run as CLI tools should use a `main()` function and the
  `if __name__ == '__main__':` guard.

### Logging
- Use Python's `logging` module. Never use bare `print()` for status or error messages in
  production scripts.
- For automation tools (watchers, schedulers), emit **structured JSON Lines logs**:
  ```python
  import json, logging
  log_data = {
      "timestamp": datetime.now().isoformat(),
      "level": "INFO",
      "module": __name__,
      "function_name": inspect.currentframe().f_code.co_name,
      "line_num": inspect.currentframe().f_lineno,
      "message": {"event_type": "analysis_start", "sample_id": sample_id}
  }
  logging.info(json.dumps(log_data))
  ```

### File I/O and paths
- Use **`pathlib.Path`** throughout. Do not concatenate paths with string joins.
- Never hardcode absolute paths. Accept input/output paths as CLI arguments.
- When reading delimited files, use **`pandas`** with explicit `dtype` and `sep` arguments.
  Do not rely on automatic type inference for sample IDs (they may look like integers).

### Error handling
- Validate inputs early. Check that input files exist and are non-empty before starting
  any analysis. Raise informative `ValueError` or `FileNotFoundError` with the file path included.
- For subprocess calls to external tools, always check the return code and capture stderr:
  ```python
  result = subprocess.run(cmd, capture_output=True, text=True)
  if result.returncode != 0:
      logging.error(f"Tool failed: {' '.join(cmd)}\nstderr: {result.stderr}")
      sys.exit(1)
  ```

### Dependencies
- List all dependencies in `environment.yml` (conda) **and** `requirements.txt` (pip-compatible
  for reference). Pin major versions.
- Standard bioinformatics libraries in use: `biopython`, `pandas`, `pysam`, `cyvcf2`.

---

## 3. R

### Style
- Follow the **tidyverse style guide**. Use `<-` for assignment, not `=`.
- Use **`tidyverse`** packages by default: `dplyr`, `tidyr`, `ggplot2`, `readr`, `purrr`.
- Avoid base R `apply` family when a `purrr` equivalent exists.
- Scripts should be runnable non-interactively: `Rscript script.R arg1 arg2`.
  Use **`optparse`** or **`argparse`** for argument parsing — do not use `commandArgs()` directly.

### Plots
- Use **`ggplot2`** for all figures. Do not use base R graphics.
- Produce output in both `.pdf` and `.png` formats unless told otherwise.
  Use `ggsave()` with explicit `width`, `height`, and `dpi = 300`.
- For phylogenetic figures, use **`ggtree`** with `treeio` for import.
  Combine with `ggplot2` geoms for metadata overlays.
- Colour palettes: use `RColorBrewer` or `viridis`. Avoid default ggplot2 rainbow palettes
  for publication figures.

### Data
- Read CSVs with `readr::read_csv()`, not `read.csv()`. Specify `col_types` explicitly
  for sample ID columns to prevent coercion to integer.
- Use **`janitor::clean_names()`** after reading external TSVs with messy headers.

---

## 4. Nextflow (DSL2)

### Structure
Pipelines must use **DSL2**. The expected layout is:

```
pipeline-name/
├── main.nf              # Workflow entry point; imports and calls modules
├── nextflow.config      # Config: params defaults, profiles, resource directives
├── modules/             # One .nf file per process
│   ├── fastp.nf
│   ├── multiqc.nf
│   └── ...
├── environments/        # One .yml per conda environment
│   └── environment.yml
├── bin/                 # Helper scripts called by processes
│   └── parse_output.py
├── assets/              # Static reference files, primer beds, etc.
├── .github/
│   └── workflows/       # CI test workflows
├── README.md
└── changelog.md
```

### Processes
- Every process must declare `tag`, `label`, `conda`/`container`, `input`, `output`,
  and `script` blocks.
- Use `tag { sample_id }` so logs identify samples clearly.
- Use `label` for resource groupings (`'process_low'`, `'process_medium'`, `'process_high'`)
  defined in `nextflow.config`.
- Outputs must use `emit:` named outputs when a process produces more than one channel.
- Do not embed long bash scripts in `script:` blocks. For logic >10 lines, call a script
  from `bin/`.

### Params and config
- All user-facing parameters go in the `params` block in `nextflow.config` with explicit defaults.
- Profiles supported: `conda` (required), `singularity` (preferred for HPC), `docker` (optional).
- Include a `--cache` / `conda.cacheDir` pattern so conda envs are shared across runs:
  ```groovy
  conda.cacheDir = params.cache ?: "$HOME/.conda/envs"
  ```

### Input modes
- Support both a **directory input** (`--fastq_input`) and a **samplesheet input**
  (`--samplesheet_input`). Samplesheet must be CSV with at minimum: `sample_id`, `fastq_r1`,
  `fastq_r2`. Validate samplesheet headers at the start of the workflow.
- FASTQ files must match: `*.fastq.gz`, `*.fq.gz`, `*.fastq`, `*.fq`.

### Output structure
```
<outdir>/
├── <sample-id>/
│   ├── <sample-id>_<tool>_output.tsv
│   ├── <sample-id>_<date>_provenance.yml
│   └── ...
├── <run-prefix>_multiqc_report.html
└── <run-prefix>_provenance.yml   # run-level provenance
```

### Provenance (mandatory)
Every pipeline must emit a **provenance YAML** per sample containing:
```yaml
- pipeline_name: BCCDC-PHL/<pipeline-name>
  pipeline_version: 0.1.0
  nextflow_session_id: <uuid>
  nextflow_run_name: <run-name>
  timestamp_analysis_start: <ISO8601>
- input_filename: sample-01_R1.fastq.gz
  file_type: fastq_input
  sha256: <checksum>
- process_name: fastp
  tools:
    - tool_name: fastp
      tool_version: 0.23.2
```
Generate SHA-256 checksums for all inputs. Capture tool versions programmatically
(e.g. `fastp --version 2>&1 | head -1`), not by hardcoding.

### Testing
- Every pipeline must have a CI test under `.github/workflows/tests.yml` that runs on
  toy/simulated data.
- Include a `--help` flag that exits cleanly without requiring inputs.

---

## 5. File Formats and Conventions

| Format | Convention |
|--------|-----------|
| Delimited tables | TSV preferred for bioinformatics outputs; CSV acceptable for reports |
| FASTA headers | Begin with sample ID: `>SAMPLE-ID_segment` |
| FASTQ filenames | `SAMPLE-ID_R1.fastq.gz` / `SAMPLE-ID_R2.fastq.gz` |
| Sample IDs | Alphanumeric + hyphens only. No spaces, underscores avoided (check existing usage) |
| Dates in filenames | ISO 8601: `YYYY-MM-DD` |
| Output prefixes | Use `<run-prefix>_<pipeline-name>_<output-type>` |

---

## 6. Common Tools — Expected Usage

The following tools are in routine use. Agents should know their standard invocations and
output formats and must not hallucinate tool names or flags that do not exist.

| Category | Tool | Notes |
|----------|------|-------|
| Read QC/trimming | `fastp`, `trimmomatic`, `trim_galore` | fastp preferred for new pipelines |
| Primer removal | `cutadapt` | |
| Alignment | `bwa mem`, `minimap2` | bwa for short reads; minimap2 for long reads |
| Variant calling | `freebayes`, `bcftools call`, `ivar` | |
| Assembly | `spades`, `dragonflye`, `flye` | |
| Annotation | `prokka`, `bakta` | |
| AMR | `AMRFinderPlus`, `ResFinder`, `tb-profiler` | |
| MLST | `mlst` (Torsten Seemann) | |
| Clade/lineage | `nextclade`, `pangolin` | |
| QC aggregation | `multiqc`, `qualimap`, `fastqc` | |
| Phylogenetics | `iqtree2`, `fasttree`, `augur` | |
| Depth normalisation | `bbnorm` (bbmap suite) | |

---

## 7. What Not to Do

- **Do not hallucinate tool names.** If you are unsure whether a tool exists, say so.
- **Do not use `shell: true`** in Python subprocess calls unless absolutely necessary.
- **Do not produce wide AMR matrices** as primary output — use tidy long format.
- **Do not omit provenance.** A pipeline output without a provenance record is incomplete.
- **Do not use relative imports** in Python scripts called from `bin/` — they are called
  from the Nextflow work directory, not the repo root.
- **Do not hard-code thread counts or memory limits.** Use Nextflow `task.cpus` and
  `task.memory`, or accept as params.
- **Do not silently drop samples.** If a sample fails a process, emit a clearly named
  failure file or log entry and continue the pipeline for other samples.

---

## 8. Domain Knowledge Notes

- **Sample IDs must be preserved exactly** throughout a pipeline. Renaming, truncating, or
  modifying sample IDs is a serious error in a public health context.
- **SNP thresholds** for cluster definition are pathogen-specific. Do not assume a universal
  value. Accept as a parameter; document the default and its source.
- **MLST novel alleles** are reported as `~` (new allele) or `-` (missing). Parsers must
  handle both without crashing.
- **Nanopore vs Illumina** data require different tools and quality thresholds. Do not apply
  Illumina-specific logic to long-read data.
- **Paired-end reads** are the default for Illumina. Always handle R1/R2 as a pair.
  Never process them independently unless the step is genuinely read-pair-agnostic.
- **Wastewater sequencing** data has different QC expectations than clinical isolates.
  Do not apply clinical thresholds to environmental samples without explicit instruction.
