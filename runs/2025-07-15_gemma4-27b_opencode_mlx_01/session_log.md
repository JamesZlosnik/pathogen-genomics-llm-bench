# Session Log — Example Reference Run

> This is a **fabricated but realistic** example run, provided so contributors
> understand what a completed session log looks like. The scores, transcript,
> and output are illustrative — not real benchmark data.

---

## Run Metadata

| Field | Value |
|-------|-------|
| Date | 2025-07-15 |
| Project | 01 — SNP Distance Matrix |
| Prompt version | `PROMPT.md v1.0` |
| Model | Gemma4-27B-Instruct |
| Quantization | Q4_K_M (GGUF) |
| Harness | OpenCode v1.4.2 |
| Provider | mlx-lm v0.22.1 |
| Provider base URL | `http://127.0.0.1:8080/v1` |
| Context window (tokens) | 32768 |
| Temperature | 0.0 (greedy) |
| Other model params | `--max-tokens 32768` |

---

## 1. Initial Prompt Delivered

```
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
3. Writes the full pairwise matrix to `results/snp_distance_matrix.csv` ...
[... full prompt as in PROMPT.md v1.0 ...]
```

---

## 2. Planning Phase

```
I'll write a Python script to compute pairwise SNP distances from a multi-sample VCF file.

Here's my plan:
1. Use cyvcf2 to parse the VCF, filtering to PASS biallelic SNPs only
2. Build a genotype array (samples × positions) — represent each genotype as
   ref (0), alt (1), or missing (-1)
3. Compute pairwise distances: for each pair, count positions where both are
   called (not -1) and genotypes differ
4. Write full matrix as CSV (pandas)
5. Write lower-triangle text table in snp-dists format
6. Filter pairs below --threshold and write transmission pairs CSV
7. Add argparse with --threshold, --help, --version

A few design choices I'll make:
- Missing genotypes (./. or .) → encoded as -1, excluded from distance counts
- Multi-allelic sites → filtered out (not biallelic)
- FILTER field → only process PASS sites
- Self-distances → always 0

Shall I proceed?
```

### Your response to the plan

```
Accepted without comment
```

---

## 3. Grill / Clarification Phase

### Question 1

**Model:** Should I treat heterozygous genotypes (0/1) as called or missing?
The prompt says "called (non-missing) genotype" but doesn't specify how to handle
hets for bacterial WGS data.

**You:** Treat 0/1 as called. For bacterial WGS at this depth, heterozygous calls
are usually mixed infections or errors — but the script should count them as called
and use the alt allele (1) for distance purposes.

### Question 2

**Model:** The prompt asks for a lower-triangle table "in the style used by snp-dists".
Should I include the header row and sample names in the left column, matching snp-dists
exact output format?

**You:** Yes — match snp-dists output format exactly, including the tab-separated
header row and sample names in column 1.

---

## 4. Execution Phase

### Actions taken (summary)

- Created `snp_distance.py` in the project root
- Attempted to run against `data/samples.vcf.gz` — `data/` directory not present
  (expected in benchmark; model correctly handled FileNotFoundError and reported it)
- Model self-corrected: added existence check at top of script with clear error message
- Wrote `results/` directory creation logic with `Path.mkdir(parents=True, exist_ok=True)`
- No retries required

### Errors / self-corrections observed

- Initial version used `variant.FILTER` directly without checking for None — model
  caught this during its own review pass and added a null check before the PASS comparison
- First attempt at lower-triangle output used `\t` join without accounting for the
  diagonal label — corrected before final output

### Full transcript

```
[opencode] Reading PROMPT.md...
[opencode] Sending to local/gemma4-27b at http://127.0.0.1:8080/v1

> Plan generated (see section 2 above)
> User accepted plan

> Clarifying questions (see section 3 above)

[opencode] Writing file: snp_distance.py
[opencode] Created snp_distance.py (187 lines)

[opencode] Running: python snp_distance.py --input data/samples.vcf.gz \
           --samples data/samples.txt --threshold 10
[opencode] Error: FileNotFoundError: data/samples.vcf.gz not found

[opencode] Model response: The input file doesn't exist in the current directory.
I'll add a clear error message and exit code for missing inputs.

[opencode] Updating: snp_distance.py
[opencode] Done. All requested output files listed in script docstring.
```

---

## 5. Final Output

| File | Present | Non-empty | Notes |
|------|---------|-----------|-------|
| `snp_distance.py` | ✅ | ✅ | 201 lines, well-commented |
| `results/snp_distance_matrix.csv` | ❌ | — | Not generated (no input data present) |
| `results/snp_distance_matrix.txt` | ❌ | — | Not generated (no input data present) |
| `results/putative_transmission_pairs.csv` | ❌ | — | Not generated (no input data present) |

> Note: output CSVs are not present because the benchmark fixture data must be
> generated separately with `python tests/generate_fixtures.py` and copied to `data/`
> before running the model's script. See `tests/README.md`.

---

## 6. Automated Test Results

```bash
# Command run:
python tests/generate_fixtures.py
cp tests/fixtures/vcf/samples.vcf.gz data/
cp tests/fixtures/samples.txt data/
python output/snp_distance.py --input data/samples.vcf.gz --samples data/samples.txt
pytest tests/test_snp_matrix.py --output-dir runs/2025-07-15_gemma4-27b_opencode_mlx_01/output/ -v

# Output:
tests/test_snp_matrix.py::test_matrix_is_square PASSED
tests/test_snp_matrix.py::test_diagonal_is_zero PASSED
tests/test_snp_matrix.py::test_matrix_is_symmetric PASSED
tests/test_snp_matrix.py::test_no_negative_values PASSED
tests/test_snp_matrix.py::test_values_are_integers PASSED
tests/test_snp_matrix.py::test_no_samples_dropped PASSED
tests/test_snp_matrix.py::test_distances_match_reference PASSED
tests/test_snp_matrix.py::test_transmission_pairs_flagged PASSED
tests/test_snp_matrix.py::test_flagged_pairs_below_threshold PASSED

9 passed in 1.24s
```

| Test | Pass/Fail |
|------|-----------|
| test_matrix_is_square | ✅ |
| test_diagonal_is_zero | ✅ |
| test_matrix_is_symmetric | ✅ |
| test_no_negative_values | ✅ |
| test_values_are_integers | ✅ |
| test_no_samples_dropped | ✅ |
| test_distances_match_reference | ✅ |
| test_transmission_pairs_flagged | ✅ |
| test_flagged_pairs_below_threshold | ✅ |

---

## 7. Evaluator Notes

- The planning phase was strong — the model identified the het-call ambiguity
  unprompted, which is a good sign of domain awareness (bacterial WGS context)
- The lower-triangle format question was reasonable; snp-dists format is not
  universally known
- The model added `--verbose` and DEBUG logging unprompted — not asked for but welcome
- Script is clean and idiomatic; uses `pathlib` throughout, `logging` not `print()`
- Minor: model used `variant.gt_types` from cyvcf2 correctly — this is a non-obvious
  API that simpler models tend to get wrong (using `variant.genotypes` directly
  and mishandling the ploidy encoding)

---

## 8. Scores

| Dimension | Score (0–4) | Notes |
|-----------|------------|-------|
| Correctness | 4 | All 9 automated tests pass; distances exactly match ground truth |
| Code Quality | 4 | Clean DSL, type hints, logging, pathlib throughout |
| Domain Appropriateness | 4 | Correctly handled het calls, PASS filter, missing GT |
| Completeness | 3 | All scripts delivered; CSVs not generated (no fixture data at run time) |
| Autonomous Execution | 3 | Two clarifying questions (both reasonable); one self-correction |
| **Total** | **18/20** | |

**Automated tests:** `9 / 9 passed (100%)`

**Time to completion:** 8 minutes
