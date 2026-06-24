# Run Evaluation

> **Fabricated reference example** — see `session_log.md` header note.

**Date:** 2025-07-15
**Model:** Gemma4-27B-Instruct Q4_K_M
**Harness:** OpenCode v1.4.2
**Provider:** mlx-lm v0.22.1
**Project:** 01 — SNP Distance Matrix

## Scores

| Dimension | Score (0–4) | Notes |
|-----------|------------|-------|
| Correctness | 4 | All 9 automated tests pass; distances match ground truth exactly |
| Code Quality | 4 | Type hints, logging, pathlib, clean separation of concerns |
| Domain Appropriateness | 4 | Correctly used `gt_types` API, handled PASS filter and missing GTs |
| Completeness | 3 | Script complete; CSVs absent at run time (no fixture data in `data/`) |
| Autonomous Execution | 3 | 2 reasonable clarifying questions; 1 self-correction during review |
| **Total** | **18 / 20** | |

## Automated Tests
`9 / 9 passed (100%)`

## Notable Strengths
- Used `cyvcf2.gt_types` correctly — a non-obvious API that models frequently
  get wrong by using `variant.genotypes` and mishandling ploidy tuples
- Proactively identified the heterozygous genotype edge case before being asked
- Added `--verbose` / DEBUG logging unprompted; follows BCCDC-PHL conventions

## Notable Issues
- None affecting correctness
- Minor: the snp-dists header line hardcodes version `0.8.2` — in production
  this should be parameterised or omitted

## Time to Completion
8 minutes
