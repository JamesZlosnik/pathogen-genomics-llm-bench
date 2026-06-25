#!/usr/bin/env python3
"""
generate_fixtures.py — Synthetic test fixture generator for pathogen-genomics-llm-bench

Generates small, deterministic, ground-truth datasets for all benchmark projects.
All random operations are seeded so outputs are reproducible across platforms.

Usage:
    python tests/generate_fixtures.py
    python tests/generate_fixtures.py --outdir tests/fixtures --seed 42 --verbose

Outputs (relative to --outdir):
    samples.txt                          — shared sample list
    vcf/samples.vcf.gz                   — multi-sample VCF  (project 08)
    expected/snp_distance_matrix.csv     — ground-truth SNP matrix
    expected/putative_transmission_pairs.csv
    amrfinder/                           — per-sample AMRFinderPlus TSVs (project 06)
    expected/amr_summary.tsv
    expected/amr_long.tsv
    fastq/reads.fastq.gz                 — synthetic FASTQ (project 03)
    expected/qc_filter_summary.txt
    assemblies/                          — FASTA assemblies (projects 08, 10)
    expected/sequence_stats.tsv
    expected/assembly_stats.tsv
    mlst/wide_table.tsv                  — wide MLST table (project 02)
    expected/long_table.tsv
    expected/sample_summary.tsv
    depth/                               — samtools depth -a style files (project 11)
    expected/depth_summary.tsv
"""

import argparse
import csv
import gzip
import json
import logging
import os
import random
import struct
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLES = [
    "SAMPLE-001", "SAMPLE-002", "SAMPLE-003", "SAMPLE-004", "SAMPLE-005",
    "SAMPLE-006", "SAMPLE-007", "SAMPLE-008", "SAMPLE-009", "SAMPLE-010",
]

CHROM = "chr1"
REF_BASES = list("ACGT")
ALT_BASES = {"A": ["C", "G", "T"], "C": ["A", "G", "T"],
             "G": ["A", "C", "T"], "T": ["A", "C", "G"]}

# Known pairwise SNP distances (upper triangle; lower is symmetric; diagonal = 0)
# Designed so SAMPLE-001/002 and SAMPLE-003/004/005 form clusters at threshold=10
SNP_DISTANCES = {
    ("SAMPLE-001", "SAMPLE-002"): 5,
    ("SAMPLE-001", "SAMPLE-003"): 42,
    ("SAMPLE-001", "SAMPLE-004"): 40,
    ("SAMPLE-001", "SAMPLE-005"): 44,
    ("SAMPLE-001", "SAMPLE-006"): 88,
    ("SAMPLE-001", "SAMPLE-007"): 91,
    ("SAMPLE-001", "SAMPLE-008"): 95,
    ("SAMPLE-001", "SAMPLE-009"): 87,
    ("SAMPLE-001", "SAMPLE-010"): 90,
    ("SAMPLE-002", "SAMPLE-003"): 44,
    ("SAMPLE-002", "SAMPLE-004"): 43,
    ("SAMPLE-002", "SAMPLE-005"): 46,
    ("SAMPLE-002", "SAMPLE-006"): 90,
    ("SAMPLE-002", "SAMPLE-007"): 88,
    ("SAMPLE-002", "SAMPLE-008"): 93,
    ("SAMPLE-002", "SAMPLE-009"): 89,
    ("SAMPLE-002", "SAMPLE-010"): 91,
    ("SAMPLE-003", "SAMPLE-004"): 3,
    ("SAMPLE-003", "SAMPLE-005"): 7,
    ("SAMPLE-003", "SAMPLE-006"): 82,
    ("SAMPLE-003", "SAMPLE-007"): 79,
    ("SAMPLE-003", "SAMPLE-008"): 84,
    ("SAMPLE-003", "SAMPLE-009"): 80,
    ("SAMPLE-003", "SAMPLE-010"): 83,
    ("SAMPLE-004", "SAMPLE-005"): 6,
    ("SAMPLE-004", "SAMPLE-006"): 81,
    ("SAMPLE-004", "SAMPLE-007"): 80,
    ("SAMPLE-004", "SAMPLE-008"): 85,
    ("SAMPLE-004", "SAMPLE-009"): 79,
    ("SAMPLE-004", "SAMPLE-010"): 82,
    ("SAMPLE-005", "SAMPLE-006"): 83,
    ("SAMPLE-005", "SAMPLE-007"): 81,
    ("SAMPLE-005", "SAMPLE-008"): 86,
    ("SAMPLE-005", "SAMPLE-009"): 82,
    ("SAMPLE-005", "SAMPLE-010"): 84,
    ("SAMPLE-006", "SAMPLE-007"): 12,
    ("SAMPLE-006", "SAMPLE-008"): 15,
    ("SAMPLE-006", "SAMPLE-009"): 9,
    ("SAMPLE-006", "SAMPLE-010"): 11,
    ("SAMPLE-007", "SAMPLE-008"): 14,
    ("SAMPLE-007", "SAMPLE-009"): 10,
    ("SAMPLE-007", "SAMPLE-010"): 13,
    ("SAMPLE-008", "SAMPLE-009"): 16,
    ("SAMPLE-008", "SAMPLE-010"): 18,
    ("SAMPLE-009", "SAMPLE-010"): 8,
}

AMR_GENE_POOL = [
    # (gene_symbol, class, subclass, sequence_name)
    ("blaTEM-1",  "BETA-LACTAM",     "AMPICILLIN",   "TEM-1 family class A beta-lactamase"),
    ("blaCTX-M-15","BETA-LACTAM",    "CEPHALOSPORIN","CTX-M-15 extended-spectrum beta-lactamase"),
    ("blaKPC-2",  "BETA-LACTAM",     "CARBAPENEM",   "KPC-2 carbapenem-hydrolyzing beta-lactamase"),
    ("blaNDM-1",  "BETA-LACTAM",     "CARBAPENEM",   "NDM-1 metallo-beta-lactamase"),
    ("aac(6')-Ib","AMINOGLYCOSIDE",  "AMIKACIN",     "Aminoglycoside acetyltransferase"),
    ("aph(3'')-Ib","AMINOGLYCOSIDE", "STREPTOMYCIN", "Aminoglycoside phosphotransferase"),
    ("sul1",      "SULFONAMIDE",     "SULFONAMIDE",  "Sulfonamide-resistant dihydropteroate synthase"),
    ("sul2",      "SULFONAMIDE",     "SULFONAMIDE",  "Sulfonamide-resistant dihydropteroate synthase 2"),
    ("dfrA1",     "TRIMETHOPRIM",    "TRIMETHOPRIM", "Dihydrofolate reductase class 1"),
    ("tet(A)",    "TETRACYCLINE",    "TETRACYCLINE", "Tetracycline efflux pump TetA"),
    ("mcr-1",     "COLISTIN",        "COLISTIN",     "Phosphoethanolamine transferase MCR-1"),
]

MLST_SCHEMES = {
    "ecoli_achtman_4": ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"],
    "klebsiella":      ["gapA", "infB", "mdh", "pgi", "phoE", "rpoB", "tonB"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_dist(a: str, b: str) -> int:
    """Return pairwise SNP distance (symmetric)."""
    key = (a, b) if (a, b) in SNP_DISTANCES else (b, a)
    return SNP_DISTANCES.get(key, 0)


def phred_char(q: int) -> str:
    return chr(q + 33)


def random_seq(length: int, rng: random.Random, gc_bias: float = 0.5) -> str:
    at = ["A", "T"]
    gc = ["G", "C"]
    return "".join(
        rng.choice(gc) if rng.random() < gc_bias else rng.choice(at)
        for _ in range(length)
    )


# ---------------------------------------------------------------------------
# Fixture generators
# ---------------------------------------------------------------------------

def write_samples(outdir: Path):
    path = outdir / "samples.txt"
    path.write_text("\n".join(SAMPLES) + "\n")
    log.info(f"Wrote {path}")


def write_snp_vcf_and_matrix(outdir: Path, rng: random.Random):
    """
    Build a multi-sample VCF whose pairwise distances exactly match SNP_DISTANCES,
    then write the ground-truth matrix and transmission pairs.
    """
    vcf_dir = outdir / "vcf"
    vcf_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(parents=True, exist_ok=True)

    n = len(SAMPLES)
    # We need enough SNP positions to encode all pairwise distances.
    # Strategy: for each pair (i,j) with dist d, assign d unique positions
    # where sample i and j differ. Use a greedy position assignment.
    # For simplicity: use one position per "distinguishing SNP" per pair,
    # packed so positions don't collide in contradictory ways.
    # Since this is synthetic and only needs to pass automated tests,
    # we construct a binary presence/absence matrix per position.

    # Simpler approach: build per-sample binary SNP vectors of length L
    # such that Hamming distance between vectors matches SNP_DISTANCES.
    # We use a random projection approach with correction.

    MAX_DIST = max(SNP_DISTANCES.values())
    L = MAX_DIST * 2  # generous number of positions

    # Random binary matrix: samples x positions
    # Then adjust pairs to match target distances exactly.
    # For a clean synthetic fixture, we use a deterministic block construction:
    # allocate position blocks for each pair.

    positions = []  # list of (pos, {sample: genotype}) for each SNP position
    pos_counter = [1000]

    def alloc_snp(sa: str, sb: str, ref: str, alt: str):
        """Add one position where sa=ref, sb=alt (or vice versa)."""
        pos_counter[0] += rng.randint(1, 10)
        gt = {s: ref for s in SAMPLES}
        gt[sb] = alt
        positions.append((pos_counter[0], ref, alt, dict(gt)))

    # For each pair, allocate exactly SNP_DISTANCES[(a,b)] positions
    # where they differ. Other samples get ref at those positions.
    for (sa, sb), dist in SNP_DISTANCES.items():
        ref = rng.choice(REF_BASES)
        alt = rng.choice(ALT_BASES[ref])
        for _ in range(dist):
            alloc_snp(sa, sb, ref, alt)

    # Add some positions where all samples are ref (should not affect distances)
    for _ in range(20):
        pos_counter[0] += rng.randint(1, 10)
        ref = rng.choice(REF_BASES)
        gt = {s: ref for s in SAMPLES}
        positions.append((pos_counter[0], ref, ref, gt))

    # Sort by position
    positions.sort(key=lambda x: x[0])

    # Write VCF
    vcf_path = vcf_dir / "samples.vcf"
    with open(vcf_path, "w") as f:
        f.write("##fileformat=VCFv4.2\n")
        f.write(f"##contig=<ID={CHROM},length=500000>\n")
        f.write('##FILTER=<ID=PASS,Description="All filters passed">\n')
        f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
        header = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"]
        header += SAMPLES
        f.write("\t".join(header) + "\n")
        for pos, ref, alt, gt_map in positions:
            row = [CHROM, str(pos), ".", ref, alt if alt != ref else ".", ".", "PASS", ".", "GT"]
            for s in SAMPLES:
                allele = gt_map[s]
                row.append("0/0" if allele == ref else "1/1")
            f.write("\t".join(row) + "\n")

    # bgzip
    vcf_gz = vcf_dir / "samples.vcf.gz"
    with open(vcf_path, "rb") as f_in:
        with gzip.open(vcf_gz, "wb") as f_out:
            f_out.write(f_in.read())
    vcf_path.unlink()
    log.info(f"Wrote {vcf_gz} ({len(positions)} positions, {n} samples)")

    # Write ground-truth SNP matrix
    matrix_path = exp_dir / "snp_distance_matrix.csv"
    with open(matrix_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + SAMPLES)
        for sa in SAMPLES:
            row = [sa]
            for sb in SAMPLES:
                row.append(str(get_dist(sa, sb)))
            writer.writerow(row)
    log.info(f"Wrote {matrix_path}")

    # Write ground-truth transmission pairs (threshold=10)
    THRESHOLD = 10
    pairs_path = exp_dir / "putative_transmission_pairs.csv"
    with open(pairs_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_a", "sample_b", "snp_distance"])
        for i, sa in enumerate(SAMPLES):
            for sb in SAMPLES[i + 1:]:
                d = get_dist(sa, sb)
                if d <= THRESHOLD:
                    writer.writerow([sa, sb, d])
    log.info(f"Wrote {pairs_path}")


def write_amrfinder_fixtures(outdir: Path, rng: random.Random):
    """Write per-sample AMRFinderPlus TSVs and ground-truth summary tables."""
    amr_dir = outdir / "amrfinder"
    amr_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(exist_ok=True)

    COLS = [
        "Protein identifier", "Contig id", "Start", "Stop", "Strand",
        "Gene symbol", "Sequence name", "Scope", "Element type",
        "Element subtype", "Class", "Subclass", "Method",
        "Target length", "Reference sequence length",
        "% Coverage of reference sequence", "% Identity to reference sequence",
        "Alignment length", "Accession of closest sequence",
        "Name of closest sequence", "HMM id", "HMM description",
    ]

    # Assign genes to samples deterministically
    sample_genes: dict[str, list] = {s: [] for s in SAMPLES}
    for i, sample in enumerate(SAMPLES):
        # Each sample gets 0-4 genes
        n_genes = rng.randint(0, 4)
        chosen = rng.sample(AMR_GENE_POOL, min(n_genes, len(AMR_GENE_POOL)))
        sample_genes[sample] = chosen

    # Ensure at least one carbapenemase sample for test coverage
    carb_genes = [g for g in AMR_GENE_POOL if g[2] == "CARBAPENEM"]
    if carb_genes:
        sample_genes[SAMPLES[2]].append(carb_genes[0])
        sample_genes[SAMPLES[2]] = list({g[0]: g for g in sample_genes[SAMPLES[2]]}.values())

    long_rows = []

    for sample in SAMPLES:
        tsv_path = amr_dir / f"{sample}_amrfinder.tsv"
        genes = sample_genes[sample]
        with open(tsv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLS, delimiter="\t")
            writer.writeheader()
            for gene_symbol, cls, subcls, seq_name in genes:
                contig = f"{sample}_contig1"
                start = rng.randint(1000, 50000)
                stop = start + rng.randint(300, 900)
                pct_cov = round(rng.uniform(95.0, 100.0), 2)
                pct_id = round(rng.uniform(95.0, 100.0), 2)
                row = {c: "" for c in COLS}
                row.update({
                    "Protein identifier": f"{sample}_{gene_symbol}",
                    "Contig id": contig,
                    "Start": str(start),
                    "Stop": str(stop),
                    "Strand": rng.choice(["+", "-"]),
                    "Gene symbol": gene_symbol,
                    "Sequence name": seq_name,
                    "Scope": "core",
                    "Element type": "AMR",
                    "Element subtype": "AMR",
                    "Class": cls,
                    "Subclass": subcls,
                    "Method": "EXACTX",
                    "Target length": str(stop - start),
                    "Reference sequence length": str(stop - start),
                    "% Coverage of reference sequence": str(pct_cov),
                    "% Identity to reference sequence": str(pct_id),
                    "Alignment length": str(stop - start),
                    "Accession of closest sequence": f"NG_{rng.randint(10000,99999)}.1",
                    "Name of closest sequence": seq_name,
                })
                writer.writerow(row)
                long_rows.append({
                    "sample_id": sample,
                    "gene_symbol": gene_symbol,
                    "class": cls,
                    "subclass": subcls,
                    "sequence_name": seq_name,
                    "scope": "core",
                    "element_type": "AMR",
                    "element_subtype": "AMR",
                    "method": "EXACTX",
                    "identity_pct": str(pct_id),
                    "coverage_pct": str(pct_cov),
                })
        log.info(f"Wrote {tsv_path} ({len(genes)} genes)")

    # Ground-truth summary
    all_classes = sorted({g[1] for g in AMR_GENE_POOL})
    summary_path = exp_dir / "amr_summary.tsv"
    with open(summary_path, "w", newline="") as f:
        fieldnames = ["sample_id"] + all_classes + ["carbapenemase_detected", "total_amr_genes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for sample in SAMPLES:
            genes = sample_genes[sample]
            row: dict = {"sample_id": sample}
            for cls in all_classes:
                gene_names = [g[0] for g in genes if g[1] == cls]
                row[cls] = ";".join(gene_names)
            row["carbapenemase_detected"] = int(any(g[2] == "CARBAPENEM" for g in genes))
            row["total_amr_genes"] = len(genes)
            writer.writerow(row)
    log.info(f"Wrote {summary_path}")

    # Ground-truth long table
    long_path = exp_dir / "amr_long.tsv"
    long_fields = ["sample_id", "gene_symbol", "class", "subclass", "sequence_name",
                   "scope", "element_type", "element_subtype", "method",
                   "identity_pct", "coverage_pct"]
    with open(long_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=long_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(long_rows)
    log.info(f"Wrote {long_path} ({len(long_rows)} rows)")


def write_fastq_fixtures(outdir: Path, rng: random.Random):
    """Write a synthetic FASTQ and ground-truth QC filter summary."""
    fq_dir = outdir / "fastq"
    fq_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(exist_ok=True)

    # Parameters
    N_READS = 1000
    MIN_LEN = 50
    MIN_QUAL = 20.0
    MAX_N_PROP = 0.05

    records = []
    counters = {"total": 0, "pass": 0, "fail_len": 0, "fail_qual": 0, "fail_n": 0, "fail_multi": 0}

    for i in range(N_READS):
        read_id = f"READ_{i+1:05d}"
        # Vary length: most pass, some fail
        if i < 50:
            length = rng.randint(20, 49)   # will fail min_length
        elif i < 60:
            length = rng.randint(200, 300)
        else:
            length = rng.randint(50, 250)

        # Vary quality
        if i < 30:
            quals = [rng.randint(5, 15) for _ in range(length)]  # fail qual
        else:
            quals = [rng.randint(20, 40) for _ in range(length)]

        # Vary N content
        seq = list(random_seq(length, rng))
        if i < 20:
            n_count = max(1, int(length * 0.10))
            for j in rng.sample(range(length), n_count):
                seq[j] = "N"
        seq_str = "".join(seq)

        n_prop = seq_str.count("N") / length
        mean_q = sum(quals) / length

        passes_len = length >= MIN_LEN
        passes_qual = mean_q >= MIN_QUAL
        passes_n = n_prop <= MAX_N_PROP
        passes = passes_len and passes_qual and passes_n

        fail_reasons = []
        if not passes_len:
            fail_reasons.append("min_length")
        if not passes_qual:
            fail_reasons.append("min_mean_qual")
        if not passes_n:
            fail_reasons.append("max_n_proportion")

        counters["total"] += 1
        if passes:
            counters["pass"] += 1
        else:
            if len(fail_reasons) > 1:
                counters["fail_multi"] += 1
            if not passes_len:
                counters["fail_len"] += 1
            if not passes_qual:
                counters["fail_qual"] += 1
            if not passes_n:
                counters["fail_n"] += 1

        qual_str = "".join(phred_char(q) for q in quals)
        records.append((read_id, seq_str, qual_str, passes))

    # Write FASTQ gz
    fq_path = fq_dir / "reads.fastq.gz"
    with gzip.open(fq_path, "wt") as f:
        for read_id, seq, qual, _ in records:
            f.write(f"@{read_id}\n{seq}\n+\n{qual}\n")
    log.info(f"Wrote {fq_path} ({N_READS} reads)")

    # Write ground-truth summary
    summary_path = exp_dir / "qc_filter_summary.txt"
    total = counters["total"]
    passing = counters["pass"]
    failing = total - passing
    with open(summary_path, "w") as f:
        f.write(f"Total reads:        {total}\n")
        f.write(f"Reads passing:      {passing} ({passing/total*100:.1f}%)\n")
        f.write(f"Reads failing:      {failing} ({failing/total*100:.1f}%)\n")
        f.write(f"  Failed min_length:       {counters['fail_len']}\n")
        f.write(f"  Failed min_mean_qual:    {counters['fail_qual']}\n")
        f.write(f"  Failed max_n_proportion: {counters['fail_n']}\n")
        f.write(f"  Failed multiple filters: {counters['fail_multi']}\n")
    log.info(f"Wrote {summary_path}")


def write_fasta_fixtures(outdir: Path, rng: random.Random):
    """Write FASTA assemblies for projects 08 and 10."""
    asm_dir = outdir / "assemblies"
    asm_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(exist_ok=True)

    # Ground truth per sample
    ground_truth = []

    for sample in SAMPLES:
        fasta_path = asm_dir / f"{sample}.fasta"
        n_contigs = rng.randint(3, 12)
        contigs = []
        for j in range(n_contigs):
            # Some contigs short (below 500bp filter), most above
            if j == n_contigs - 1 and n_contigs > 3:
                length = rng.randint(100, 499)  # will be filtered
            else:
                length = rng.randint(500, 50000)
            gc_bias = rng.uniform(0.45, 0.65)
            seq = random_seq(length, rng, gc_bias)
            # Add some Ns
            n_count = rng.randint(0, max(1, length // 100))
            seq_list = list(seq)
            for pos in rng.sample(range(length), min(n_count, length)):
                seq_list[pos] = "N"
            seq = "".join(seq_list)
            contigs.append((f"{sample}_contig{j+1}", seq))

        with open(fasta_path, "w") as f:
            for name, seq in contigs:
                f.write(f">{name}\n")
                for start in range(0, len(seq), 60):
                    f.write(seq[start:start+60] + "\n")

        # Compute ground truth for this sample (filtered: length >= 500)
        filtered = [(n, s) for n, s in contigs if len(s) >= 500]
        lengths = sorted([len(s) for _, s in filtered], reverse=True)
        total_len = sum(lengths)
        cumsum = 0
        n50 = 0
        l50 = 0
        for idx, ln in enumerate(lengths):
            cumsum += ln
            if cumsum >= total_len * 0.5 and n50 == 0:
                n50 = ln
                l50 = idx + 1
        cumsum = 0
        n90 = 0
        for ln in lengths:
            cumsum += ln
            if cumsum >= total_len * 0.9 and n90 == 0:
                n90 = ln

        all_seqs = "".join(s for _, s in filtered)
        n_bases = all_seqs.count("N") + all_seqs.count("n")
        non_n = len(all_seqs) - n_bases
        gc = sum(all_seqs.count(b) for b in "GCgc")
        gc_pct = round(gc / non_n * 100, 4) if non_n > 0 else 0.0

        ground_truth.append({
            "sample_id": sample,
            "total_contigs": len(contigs),
            "filtered_contigs": len(filtered),
            "total_length_bp": total_len,
            "largest_contig_bp": max(lengths) if lengths else 0,
            "n50_bp": n50,
            "n90_bp": n90,
            "l50": l50,
            "gc_pct": gc_pct,
            "n_count": n_bases,
            "n_proportion": round(n_bases / total_len, 4) if total_len > 0 else 0.0,
        })
        log.info(f"Wrote {fasta_path} ({len(contigs)} contigs, {len(filtered)} filtered)")

    # Write ground-truth assembly stats
    asm_stats_path = exp_dir / "assembly_stats.tsv"
    fields = ["sample_id", "total_contigs", "filtered_contigs", "total_length_bp",
              "largest_contig_bp", "n50_bp", "n90_bp", "l50", "gc_pct",
              "n_count", "n_proportion"]
    with open(asm_stats_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(ground_truth)
    log.info(f"Wrote {asm_stats_path}")

    # Write ground-truth sequence stats (project 01 — single FASTA, use SAMPLE-001)
    sample_01_path = asm_dir / "SAMPLE-001.fasta"
    seq_stats_path = exp_dir / "sequence_stats.tsv"
    from Bio import SeqIO  # type: ignore
    rows = []
    for rec in SeqIO.parse(sample_01_path, "fasta"):
        seq = str(rec.seq)
        n_count = seq.upper().count("N")
        non_n = len(seq) - n_count
        gc = sum(seq.upper().count(b) for b in "GC")
        gc_pct = round(gc / non_n * 100, 4) if non_n > 0 else "NA"
        rows.append({
            "seq_id": rec.id,
            "description": rec.description,
            "length_bp": len(seq),
            "gc_pct": gc_pct,
            "n_count": n_count,
            "n_proportion": round(n_count / len(seq), 4),
        })
    with open(seq_stats_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seq_id","description","length_bp",
                                                "gc_pct","n_count","n_proportion"],
                                delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"Wrote {seq_stats_path}")


def write_mlst_fixtures(outdir: Path, rng: random.Random):
    """Write wide-format MLST table and ground-truth long/summary tables."""
    mlst_dir = outdir / "mlst"
    mlst_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(exist_ok=True)

    scheme = "ecoli_achtman_4"
    loci = MLST_SCHEMES[scheme]

    rows_wide = []
    rows_long = []
    rows_summary = []

    for i, sample in enumerate(SAMPLES):
        st = rng.randint(10, 999)
        alleles = {}
        for locus in loci:
            r = rng.random()
            if r < 0.05:
                alleles[locus] = "-"          # missing
            elif r < 0.10:
                alleles[locus] = f"~{rng.randint(100,999)}"  # novel
            elif r < 0.13:
                alleles[locus] = f"{rng.randint(1,50)}?"     # uncertain
            else:
                alleles[locus] = str(rng.randint(1, 50))

        # Force SAMPLE-001 to have a novel ST
        if i == 0:
            st_str = "-"
        else:
            st_str = str(st)

        wide_row = {"sample_id": sample, "scheme": scheme, "st": st_str}
        wide_row.update(alleles)
        rows_wide.append(wide_row)

        missing = sum(1 for v in alleles.values() if v == "-")
        novel = sum(1 for v in alleles.values() if v.startswith("~"))
        uncertain = sum(1 for v in alleles.values() if v.endswith("?") and not v.startswith("~"))
        rows_summary.append({
            "sample_id": sample,
            "scheme": scheme,
            "st": st_str,
            "total_loci": len(loci),
            "missing_loci": missing,
            "novel_loci": novel,
            "uncertain_loci": uncertain,
            "complete": int(missing == 0 and novel == 0),
        })

        for locus in loci:
            allele_val = alleles[locus]
            if allele_val == "-":
                status = "missing"
            elif allele_val.startswith("~"):
                status = "novel"
            elif allele_val.endswith("?"):
                status = "uncertain"
            elif allele_val.isdigit():
                status = "integer"
            else:
                status = "other"
            rows_long.append({
                "sample_id": sample,
                "scheme": scheme,
                "st": st_str,
                "locus": locus,
                "allele": allele_val,
                "allele_status": status,
            })

    # Wide table
    wide_path = mlst_dir / "wide_table.tsv"
    wide_fields = ["sample_id", "scheme", "st"] + loci
    with open(wide_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=wide_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows_wide)
    log.info(f"Wrote {wide_path}")

    # Ground-truth long table
    long_path = exp_dir / "long_table.tsv"
    long_fields = ["sample_id", "scheme", "st", "locus", "allele", "allele_status"]
    with open(long_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=long_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows_long)
    log.info(f"Wrote {long_path}")

    # Ground-truth summary
    summary_path = exp_dir / "sample_summary.tsv"
    sum_fields = ["sample_id", "scheme", "st", "total_loci", "missing_loci",
                  "novel_loci", "uncertain_loci", "complete"]
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sum_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows_summary)
    log.info(f"Wrote {summary_path}")


def write_depth_fixtures(outdir: Path, rng: random.Random):
    """Write samtools depth -a style files and ground-truth summary."""
    depth_dir = outdir / "depth"
    depth_dir.mkdir(parents=True, exist_ok=True)
    exp_dir = outdir / "expected"
    exp_dir.mkdir(exist_ok=True)

    CONTIGS = [("contig1", 5000), ("contig2", 3000), ("contig3", 2000)]
    LOW_COV_THRESHOLD = 90.0

    summary_rows = []

    for i, sample in enumerate(SAMPLES):
        depth_path = depth_dir / f"{sample}.depth.tsv"
        all_depths = []

        with open(depth_path, "w") as f:
            for contig, length in CONTIGS:
                mean_d = rng.randint(5, 150)
                # SAMPLE-010 gets deliberately low coverage
                if i == 9:
                    mean_d = rng.randint(1, 4)
                for pos in range(1, length + 1):
                    d = max(0, int(rng.gauss(mean_d, mean_d * 0.3)))
                    f.write(f"{contig}\t{pos}\t{d}\n")
                    all_depths.append(d)

        # Compute genome-wide ground truth
        total = len(all_depths)
        mean_d = round(sum(all_depths) / total, 4)
        sorted_d = sorted(all_depths)
        median_d = sorted_d[total // 2]
        min_d = sorted_d[0]
        max_d = sorted_d[-1]
        pct_1x = round(sum(1 for d in all_depths if d >= 1) / total * 100, 4)
        pct_10x = round(sum(1 for d in all_depths if d >= 10) / total * 100, 4)
        pct_20x = round(sum(1 for d in all_depths if d >= 20) / total * 100, 4)
        pct_100x = round(sum(1 for d in all_depths if d >= 100) / total * 100, 4)
        low_cov = int(pct_10x < LOW_COV_THRESHOLD)

        summary_rows.append({
            "sample_id": sample,
            "mean_depth": mean_d,
            "median_depth": median_d,
            "min_depth": min_d,
            "max_depth": max_d,
            "pct_covered_1x": pct_1x,
            "pct_covered_10x": pct_10x,
            "pct_covered_20x": pct_20x,
            "pct_covered_100x": pct_100x,
            "total_positions": total,
            "low_coverage": low_cov,
        })
        log.info(f"Wrote {depth_path} ({total} positions)")

    summary_path = exp_dir / "depth_summary.tsv"
    fields = ["sample_id", "mean_depth", "median_depth", "min_depth", "max_depth",
              "pct_covered_1x", "pct_covered_10x", "pct_covered_20x",
              "pct_covered_100x", "total_positions", "low_coverage"]
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(summary_rows)
    log.info(f"Wrote {summary_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic benchmark fixtures for pathogen-genomics-llm-bench"
    )
    parser.add_argument("--outdir", default="tests/fixtures",
                        help="Output directory (default: tests/fixtures)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable DEBUG logging")
    parser.add_argument("--skip-biopython", action="store_true",
                        help="Skip steps requiring Biopython (sequence_stats.tsv)")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    log.info(f"Generating fixtures in: {outdir.resolve()}")
    log.info(f"Random seed: {args.seed}")
    log.info(f"Samples: {SAMPLES}")

    write_samples(outdir)
    write_snp_vcf_and_matrix(outdir, rng)
    write_amrfinder_fixtures(outdir, rng)
    write_fastq_fixtures(outdir, rng)

    try:
        from Bio import SeqIO  # noqa: F401
        write_fasta_fixtures(outdir, rng)
    except ImportError:
        if args.skip_biopython:
            log.warning("Biopython not installed — skipping FASTA fixtures (projects 08, 10)")
        else:
            log.error("Biopython not installed. Run: pip install biopython")
            log.error("Or re-run with --skip-biopython to skip FASTA fixtures")
            sys.exit(1)

    write_mlst_fixtures(outdir, rng)
    write_depth_fixtures(outdir, rng)

    log.info("Done. Fixture manifest:")
    for path in sorted(outdir.rglob("*")):
        if path.is_file():
            size = path.stat().st_size
            log.info(f"  {path.relative_to(outdir)}  ({size:,} bytes)")


if __name__ == "__main__":
    main()
