# Project 04 — Nextflow QC Pipeline
## No-Plan / No-Grill Prompt Variant v1.0

> **Instructions for use:** Use this variant when testing models in a mode that skips the
> planning/clarification phase. The task is identical to `PROMPT.md` but the final
> paragraph instructs the model to proceed without asking questions.

---

Please write a Nextflow DSL2 pipeline called `illumina-qc-nf` that performs quality
control on paired-end Illumina FASTQ files. The pipeline should:

**Processes (in order):**
1. `FASTQC_RAW` — run FastQC on raw R1 and R2 reads
2. `FASTP` — trim adapters and low-quality bases using fastp. Emit a JSON report and
   a filtered R1/R2 pair per sample.
3. `FASTQC_TRIMMED` — run FastQC on the trimmed R1 and R2 reads
4. `MULTIQC` — aggregate all FastQC and fastp reports into a single MultiQC HTML report

**Input modes — support both:**
- `--fastq_input <dir>` — directory of paired FASTQ files matching `*_R{1,2}*.fastq.gz`
- `--samplesheet_input <csv>` — CSV with columns `sample_id`, `fastq_r1`, `fastq_r2`

**Required structure:**
```
illumina-qc-nf/
├── main.nf
├── nextflow.config
├── modules/
│   ├── fastqc.nf
│   ├── fastp.nf
│   └── multiqc.nf
└── environments/
    └── qc.yml
```

**nextflow.config must include:**
- A `params` block with defaults for: `fastq_input`, `samplesheet_input`, `outdir`
  (default: `results`), `cache` (conda cache dir), fastp `min_length` (default: 50),
  fastp `qualified_quality_phred` (default: 20)
- Resource labels: `process_low` (1 CPU, 2 GB), `process_medium` (4 CPU, 8 GB)
- Profiles: `conda` and `singularity`
- `conda.cacheDir = params.cache ?: "$HOME/.conda/nf-cache"`

**Each process must have:** `tag`, `label`, `conda`/`container`, `input`, `output`
with named `emit:` blocks, and `script`.

**Output directory structure:**
```
results/
├── <sample_id>/
│   ├── <sample_id>_fastqc_raw/
│   ├── <sample_id>_fastp.json
│   ├── <sample_id>_R1_trimmed.fastq.gz
│   ├── <sample_id>_R2_trimmed.fastq.gz
│   └── <sample_id>_fastqc_trimmed/
└── multiqc/
    └── multiqc_report.html
```

**`environments/qc.yml`** must be a valid conda environment file pinning: `fastqc`,
`fastp`, `multiqc`.

The pipeline must support `--help` (print usage and exit cleanly).

Do not embed logic longer than 5 lines in `script:` blocks — use scripts in `bin/`
for any parsing or summarisation steps.


Do not ask any clarifying questions. Make reasonable assumptions where needed, state them
briefly in a comment at the top of the script, and proceed directly to writing the code.

Input: paired-end FASTQ files (directory or samplesheet)
Output: FastQC reports, trimmed FASTQs, fastp JSON reports, MultiQC HTML
