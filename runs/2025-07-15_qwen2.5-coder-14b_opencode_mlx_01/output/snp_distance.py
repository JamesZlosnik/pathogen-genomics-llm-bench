#!/usr/bin/env python3
"""
snp_distance.py — Compute pairwise SNP distance matrix from a multi-sample VCF.

Assumptions (stated at model planning phase):
- Heterozygous genotypes (0/1) are treated as called; alt allele used for distance
- Only PASS, biallelic SNP sites are considered
- Missing genotypes (./.) are excluded from pairwise distance counts
- Self-distances are always 0

Version: 1.0.0
"""

import argparse
import logging
import sys
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from cyvcf2 import VCF

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute pairwise SNP distance matrix from a multi-sample VCF."
    )
    parser.add_argument("--input", required=True,
                        help="Path to multi-sample VCF or VCF.gz")
    parser.add_argument("--samples", default="data/samples.txt",
                        help="File listing sample IDs, one per line (default: data/samples.txt)")
    parser.add_argument("--outdir", default="results",
                        help="Output directory (default: results)")
    parser.add_argument("--threshold", type=int, default=10,
                        help="SNP distance threshold for putative transmission pairs (default: 10)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable DEBUG logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def load_samples(samples_file: Path) -> list[str]:
    if not samples_file.exists():
        log.error(f"Samples file not found: {samples_file}")
        sys.exit(1)
    samples = [line.strip() for line in samples_file.read_text().splitlines() if line.strip()]
    log.info(f"Loaded {len(samples)} sample IDs from {samples_file}")
    return samples


def parse_vcf(vcf_path: Path, expected_samples: list[str]) -> tuple[list[str], np.ndarray]:
    """
    Parse a multi-sample VCF and return (sample_list, genotype_matrix).

    Genotype matrix shape: (n_samples, n_sites)
    Values: 0 = ref, 1 = alt, -1 = missing
    Only PASS, biallelic SNP sites are included.
    """
    if not vcf_path.exists():
        log.error(f"VCF file not found: {vcf_path}")
        sys.exit(1)

    vcf = VCF(str(vcf_path))
    vcf_samples = list(vcf.samples)
    log.info(f"VCF contains {len(vcf_samples)} samples")

    # Validate sample overlap
    missing = set(expected_samples) - set(vcf_samples)
    if missing:
        log.error(f"Samples in sample list not found in VCF: {missing}")
        sys.exit(1)

    sample_idx = [vcf_samples.index(s) for s in expected_samples]

    site_genotypes: list[list[int]] = []  # one list per PASS biallelic SNP
    n_sites_total = 0
    n_sites_pass = 0

    for variant in vcf:
        n_sites_total += 1

        # FILTER check
        filters = variant.FILTER
        if filters is not None and filters != "PASS":
            continue

        # Biallelic SNP check
        if len(variant.ALT) != 1:
            continue
        ref, alt = variant.REF, variant.ALT[0]
        if len(ref) != 1 or len(alt) != 1:
            continue  # not a SNP (indel)

        n_sites_pass += 1

        # gt_types: 0=HOM_REF, 1=HET, 2=UNKNOWN, 3=HOM_ALT
        gt_types = variant.gt_types
        row: list[int] = []
        for idx in sample_idx:
            gt = gt_types[idx]
            if gt == 0:       # HOM_REF
                row.append(0)
            elif gt == 3:     # HOM_ALT
                row.append(1)
            elif gt == 1:     # HET — treat as alt (see assumptions)
                row.append(1)
            else:             # UNKNOWN / missing
                row.append(-1)
        site_genotypes.append(row)

    log.info(f"Parsed {n_sites_total} sites total; {n_sites_pass} PASS biallelic SNPs retained")

    if not site_genotypes:
        log.warning("No PASS biallelic SNP sites found in VCF")
        return expected_samples, np.empty((len(expected_samples), 0), dtype=int)

    # Shape: (n_sites, n_samples) → transpose to (n_samples, n_sites)
    gt_matrix = np.array(site_genotypes, dtype=int).T
    return expected_samples, gt_matrix


def compute_distance_matrix(samples: list[str], gt_matrix: np.ndarray) -> pd.DataFrame:
    """
    Compute pairwise SNP distances.
    Distance(A, B) = number of sites where both are called and genotypes differ.
    """
    n = len(samples)
    dist = np.zeros((n, n), dtype=int)

    for i, j in combinations(range(n), 2):
        gt_i = gt_matrix[i]
        gt_j = gt_matrix[j]
        # Both called (not -1)
        both_called = (gt_i >= 0) & (gt_j >= 0)
        # Differ
        differ = gt_i != gt_j
        d = int(np.sum(both_called & differ))
        dist[i, j] = d
        dist[j, i] = d

    return pd.DataFrame(dist, index=samples, columns=samples)


def write_matrix_csv(df: pd.DataFrame, outdir: Path) -> Path:
    path = outdir / "snp_distance_matrix.csv"
    df.to_csv(path)
    log.info(f"Wrote {path}")
    return path


def write_lower_triangle(df: pd.DataFrame, outdir: Path) -> Path:
    """Write lower-triangle table in snp-dists format."""
    samples = list(df.index)
    path = outdir / "snp_distance_matrix.txt"
    with open(path, "w") as f:
        # Header row
        f.write("\t".join(["snp-dists 0.8.2"] + samples) + "\n")
        for i, sa in enumerate(samples):
            row_vals = [str(df.loc[sa, sb]) for sb in samples[: i + 1]]
            f.write("\t".join([sa] + row_vals) + "\n")
    log.info(f"Wrote {path}")
    return path


def write_transmission_pairs(df: pd.DataFrame, threshold: int, outdir: Path) -> Path:
    samples = list(df.index)
    path = outdir / "putative_transmission_pairs.csv"
    rows = []
    for i, sa in enumerate(samples):
        for sb in samples[i + 1 :]:
            d = int(df.loc[sa, sb])
            if d <= threshold:
                rows.append({"sample_a": sa, "sample_b": sb, "snp_distance": d})
    pairs_df = pd.DataFrame(rows, columns=["sample_a", "sample_b", "snp_distance"])
    pairs_df.to_csv(path, index=False)
    log.info(f"Wrote {path} ({len(rows)} pairs at threshold ≤{threshold})")
    return path


def main():
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    vcf_path = Path(args.input)
    samples_file = Path(args.samples)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    samples = load_samples(samples_file)
    samples, gt_matrix = parse_vcf(vcf_path, samples)
    dist_df = compute_distance_matrix(samples, gt_matrix)

    write_matrix_csv(dist_df, outdir)
    write_lower_triangle(dist_df, outdir)
    write_transmission_pairs(dist_df, args.threshold, outdir)

    n = len(samples)
    n_pairs = n * (n - 1) // 2
    n_transmission = int((dist_df.values[~np.eye(n, dtype=bool)] <= args.threshold).sum() // 2)

    print(f"Total samples:             {n}")
    print(f"Total pairwise comparisons: {n_pairs}")
    print(f"Pairs below threshold (≤{args.threshold}): {n_transmission}")


if __name__ == "__main__":
    main()
