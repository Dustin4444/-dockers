"""Benchmarks for the notebook inspection workload.

The inputs are the notebooks committed in this repository, so the benchmarks
grow with the real content of the project.
"""

from __future__ import annotations

import pytest

from workloads import (
    extract_code,
    notebook_stats,
    parse_notebook,
    read_notebook,
    strip_outputs,
)

NOTEBOOKS = {
    "tensorflow_quickstart": "tensorflow_quickstart.ipynb",
    "mistral_ocr_tool_usage": "mistral/ocr/tool_usage.ipynb",
}


@pytest.fixture(scope="session", params=sorted(NOTEBOOKS), ids=sorted(NOTEBOOKS))
def notebook_name(request) -> str:
    return request.param


@pytest.fixture(scope="session")
def raw_notebook(notebook_name: str) -> str:
    return read_notebook(NOTEBOOKS[notebook_name])


@pytest.fixture(scope="session")
def notebook(raw_notebook: str) -> dict:
    return parse_notebook(raw_notebook)


def test_parse_notebook(benchmark, raw_notebook: str) -> None:
    parsed = benchmark(parse_notebook, raw_notebook)
    assert parsed["cells"]


def test_extract_code(benchmark, notebook: dict) -> None:
    code = benchmark(extract_code, notebook)
    assert isinstance(code, str)


def test_notebook_stats(benchmark, notebook: dict) -> None:
    stats = benchmark(notebook_stats, notebook)
    assert stats


def test_strip_outputs(benchmark, notebook: dict) -> None:
    cleaned = benchmark(strip_outputs, notebook)
    assert cleaned.startswith("{")
