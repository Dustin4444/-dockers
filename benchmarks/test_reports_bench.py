"""Benchmarks for the Snyk/SARIF report processing workload."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks.workloads import (
    analyze_sarif,
    extract_findings,
    make_sarif_report,
    parse_sarif,
    summarize_findings,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMITTED_REPORTS = (
    "snyk_code_results.json",
    "snyk_iac_results.json",
    "snyk_sca_results.json",
)
FINDING_COUNTS = (100, 2_500, 25_000)


@pytest.mark.parametrize("size", FINDING_COUNTS)
def test_parse_sarif(benchmark, size: int) -> None:
    raw = make_sarif_report(size)
    report = benchmark(parse_sarif, raw)
    assert report["version"] == "2.1.0"


@pytest.mark.parametrize("size", FINDING_COUNTS)
def test_extract_findings(benchmark, size: int) -> None:
    report = parse_sarif(make_sarif_report(size))
    findings = benchmark(extract_findings, report)
    assert len(findings) == size


@pytest.mark.parametrize("size", FINDING_COUNTS)
def test_summarize_findings(benchmark, size: int) -> None:
    findings = extract_findings(parse_sarif(make_sarif_report(size)))
    summary = benchmark(summarize_findings, findings)
    assert summary["total"] == size


@pytest.mark.parametrize("size", FINDING_COUNTS)
def test_analyze_sarif_pipeline(benchmark, size: int) -> None:
    raw = make_sarif_report(size)
    summary = benchmark(analyze_sarif, raw)
    assert summary["total"] == size


@pytest.mark.parametrize("filename", COMMITTED_REPORTS)
def test_parse_committed_report(benchmark, filename: str) -> None:
    raw = (REPO_ROOT / filename).read_text(encoding="utf-8")
    report = benchmark(parse_sarif, raw)
    assert isinstance(report, dict)
