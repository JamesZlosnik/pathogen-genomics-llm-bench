"""
conftest.py — Shared pytest configuration for pathogen-genomics-llm-bench tests.

Provides:
- --output-dir CLI option: points pytest at a model run's output directory
- --fixtures-dir CLI option: points pytest at the generated fixture data
- Shared fixtures: output_dir, fixtures_dir, expected_dir
"""

import os
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--output-dir",
        action="store",
        default=None,
        help="Path to the model run's output directory (runs/.../output/)",
    )
    parser.addoption(
        "--fixtures-dir",
        action="store",
        default="tests/fixtures",
        help="Path to generated fixture data (default: tests/fixtures)",
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def output_dir(request) -> Path:
    """
    Path to the model run's output directory.
    Skip all tests in a module if not provided.
    """
    d = request.config.getoption("--output-dir")
    if d is None:
        pytest.skip("No --output-dir provided. "
                    "Run with: pytest tests/ --output-dir runs/<run>/output/")
    path = Path(d)
    if not path.exists():
        pytest.fail(f"Output directory does not exist: {path}")
    return path


@pytest.fixture(scope="session")
def fixtures_dir(request) -> Path:
    """Path to the synthetic fixture data directory."""
    d = request.config.getoption("--fixtures-dir")
    path = Path(d)
    if not path.exists():
        pytest.fail(
            f"Fixtures directory not found: {path}\n"
            f"Generate fixtures first with: python tests/generate_fixtures.py"
        )
    return path


@pytest.fixture(scope="session")
def expected_dir(fixtures_dir) -> Path:
    """Path to the expected (ground-truth) outputs within fixtures."""
    path = fixtures_dir / "expected"
    if not path.exists():
        pytest.fail(
            f"Expected outputs directory not found: {path}\n"
            f"Re-run: python tests/generate_fixtures.py"
        )
    return path


@pytest.fixture(scope="session")
def samples(fixtures_dir) -> list[str]:
    """Load the canonical sample list from fixtures."""
    samples_file = fixtures_dir / "samples.txt"
    if not samples_file.exists():
        pytest.fail(f"samples.txt not found in fixtures: {samples_file}")
    return [line.strip() for line in samples_file.read_text().splitlines()
            if line.strip()]


# ---------------------------------------------------------------------------
# Helpers available to all test modules
# ---------------------------------------------------------------------------

def find_output_file(output_dir: Path, keywords: list[str],
                     extensions: list[str] | None = None) -> Path | None:
    """
    Search output_dir for a file whose name contains any of the keywords
    and (optionally) has one of the given extensions.

    Returns the first match, or None if not found.
    """
    extensions = extensions or [".csv", ".tsv", ".txt", ".html", ".pdf", ".png"]
    candidates = [
        f for f in output_dir.rglob("*")
        if f.is_file()
        and any(kw.lower() in f.name.lower() for kw in keywords)
        and f.suffix.lower() in extensions
    ]
    return candidates[0] if candidates else None


def assert_output_exists(output_dir: Path, keywords: list[str],
                          extensions: list[str] | None = None,
                          label: str = "") -> Path:
    """
    Assert that an output file matching keywords exists.
    Returns the path for further inspection.
    Fails the test with a helpful message if not found.
    """
    path = find_output_file(output_dir, keywords, extensions)
    if path is None:
        label_str = f" ({label})" if label else ""
        pytest.fail(
            f"Expected output file{label_str} not found in {output_dir}\n"
            f"Looked for files containing: {keywords}\n"
            f"With extensions: {extensions or ['.csv','.tsv','.txt','.html','.pdf','.png']}\n"
            f"Files present:\n" +
            "\n".join(f"  {f.name}" for f in sorted(output_dir.rglob("*")) if f.is_file())
        )
    return path
