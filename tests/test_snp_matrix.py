"""
Tests for Project 01 — SNP Distance Matrix

Validates model-generated scripts by running them against fixture data
and checking outputs against known-correct reference values.

Usage:
    pytest tests/test_snp_matrix.py --output-dir <path_to_run_output> -v
"""

import os
import subprocess
import pytest
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Fixtures / paths
# ---------------------------------------------------------------------------

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "expected_outputs")
EXPECTED_MATRIX = os.path.join(FIXTURES, "snp_matrix.csv")


def pytest_addoption(parser):
    parser.addoption(
        "--output-dir",
        action="store",
        default=None,
        help="Path to the model run's output directory",
    )


@pytest.fixture
def output_dir(request):
    d = request.config.getoption("--output-dir")
    if d is None:
        pytest.skip("No --output-dir provided")
    return d


@pytest.fixture
def model_matrix(output_dir):
    """Find and load the model-produced SNP distance CSV."""
    candidates = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
    if not candidates:
        pytest.fail(f"No CSV file found in {output_dir}")
    # Prefer a file with 'distance' or 'snp' in the name
    preferred = [c for c in candidates if any(k in c.lower() for k in ("distance", "snp", "matrix"))]
    path = os.path.join(output_dir, preferred[0] if preferred else candidates[0])
    df = pd.read_csv(path, index_col=0)
    return df


@pytest.fixture
def expected_matrix():
    df = pd.read_csv(EXPECTED_MATRIX, index_col=0)
    return df


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------

def test_matrix_is_square(model_matrix):
    """Matrix must have equal number of rows and columns."""
    assert model_matrix.shape[0] == model_matrix.shape[1], (
        f"Matrix is not square: {model_matrix.shape}"
    )


def test_diagonal_is_zero(model_matrix):
    """Self-distances must be zero."""
    diag = np.diag(model_matrix.values.astype(float))
    assert np.all(diag == 0), f"Non-zero diagonal values: {diag}"


def test_matrix_is_symmetric(model_matrix):
    """SNP distances must be symmetric: dist(A,B) == dist(B,A)."""
    vals = model_matrix.values.astype(float)
    assert np.allclose(vals, vals.T, atol=0), "Matrix is not symmetric"


def test_no_negative_values(model_matrix):
    """All distances must be non-negative."""
    assert (model_matrix.values.astype(float) >= 0).all(), "Negative distances found"


def test_values_are_integers(model_matrix):
    """SNP distances should be whole numbers."""
    vals = model_matrix.values.astype(float)
    # Allow diagonal zeros
    off_diag = vals[~np.eye(vals.shape[0], dtype=bool)]
    assert np.all(off_diag == off_diag.astype(int)), "Non-integer SNP distances found"


def test_no_samples_dropped(model_matrix, expected_matrix):
    """Model must not silently drop samples."""
    expected_samples = set(expected_matrix.index)
    model_samples = set(model_matrix.index)
    missing = expected_samples - model_samples
    assert not missing, f"Samples missing from output: {missing}"


# ---------------------------------------------------------------------------
# Correctness tests
# ---------------------------------------------------------------------------

def test_distances_match_reference(model_matrix, expected_matrix):
    """All pairwise distances must match the reference within tolerance."""
    # Align on shared samples in same order
    shared = sorted(set(model_matrix.index) & set(expected_matrix.index))
    m = model_matrix.loc[shared, shared].values.astype(float)
    e = expected_matrix.loc[shared, shared].values.astype(float)
    assert np.allclose(m, e, atol=0), (
        f"Distance matrix does not match reference.\n"
        f"Max diff: {np.max(np.abs(m - e))}"
    )


# ---------------------------------------------------------------------------
# Threshold flagging tests
# ---------------------------------------------------------------------------

def test_transmission_pairs_flagged(output_dir):
    """Check that a pairs file or flagged output exists when threshold is set."""
    # Accept any CSV/TSV that looks like a pairs file
    candidates = [
        f for f in os.listdir(output_dir)
        if any(k in f.lower() for k in ("pair", "cluster", "flag", "transmission"))
    ]
    assert candidates, (
        "No transmission pairs / flagged pairs file found in output. "
        "Expected a file with 'pair', 'cluster', 'flag', or 'transmission' in the name."
    )


def test_flagged_pairs_below_threshold(output_dir):
    """All flagged pairs must have distance ≤ threshold (default 10)."""
    THRESHOLD = 10
    candidates = [
        f for f in os.listdir(output_dir)
        if any(k in f.lower() for k in ("pair", "flag", "transmission"))
        and f.endswith((".csv", ".tsv"))
    ]
    if not candidates:
        pytest.skip("No flagged pairs file to check")

    path = os.path.join(output_dir, candidates[0])
    sep = "\t" if path.endswith(".tsv") else ","
    df = pd.read_csv(path, sep=sep)

    # Look for a distance-like column
    dist_cols = [c for c in df.columns if any(k in c.lower() for k in ("dist", "snp", "diff"))]
    if not dist_cols:
        pytest.skip("Could not identify distance column in pairs file")

    distances = df[dist_cols[0]].values.astype(float)
    assert np.all(distances <= THRESHOLD), (
        f"Flagged pairs with distance > {THRESHOLD}: {distances[distances > THRESHOLD]}"
    )
