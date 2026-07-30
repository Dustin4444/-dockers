"""Workloads exercised by the CodSpeed benchmarks.

The repository is a Copilot + Codespaces playground: the demo scripts
(`convert_comments_to_code.py`, `json_to_user.py`) are intentionally left
incomplete for the CodeTours, so they cannot be imported. This module gathers
reference implementations of the two data-processing workloads the repository
actually deals with:

* JSON <-> ``User`` conversion, the exercise described in ``json_to_user.py``
* notebook inspection, applied to the ``.ipynb`` files stored in the repository
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class User:
    """Same shape as the ``User`` class of ``json_to_user.py``."""

    __slots__ = ("name", "email", "password")

    def __init__(self, name: str, email: str, password: str) -> None:
        self.name = name
        self.email = email
        self.password = password


def create_user(payload: dict) -> User:
    """Build a ``User`` from a decoded JSON object."""
    return User(payload["name"], payload["email"], payload["password"])


def jsonify_user(user: User) -> str:
    """Serialize a ``User`` back to a JSON string."""
    return json.dumps(
        {"name": user.name, "email": user.email, "password": user.password}
    )


def make_user_payloads(count: int) -> list[dict]:
    """Generate a deterministic list of user payloads."""
    return [
        {
            "name": f"User {index}",
            "email": f"user{index}@example.com",
            "password": f"password{index}",
        }
        for index in range(count)
    ]


def load_users(raw: str) -> list[User]:
    """Decode a JSON array of user objects into ``User`` instances."""
    return [create_user(payload) for payload in json.loads(raw)]


def dump_users(users: list[User]) -> str:
    """Serialize a list of ``User`` instances to a JSON array."""
    return "[" + ",".join(jsonify_user(user) for user in users) + "]"


def read_notebook(relative_path: str) -> str:
    """Read one of the notebooks stored in the repository."""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def parse_notebook(raw: str) -> dict:
    """Decode a notebook document."""
    return json.loads(raw)


def cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def extract_code(notebook: dict) -> str:
    """Concatenate the source of every code cell of a notebook."""
    return "\n".join(
        cell_source(cell)
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    )


def notebook_stats(notebook: dict) -> dict:
    """Compute per-cell-type counts, line counts and character counts."""
    stats: dict[str, dict[str, int]] = {}
    for cell in notebook.get("cells", []):
        entry = stats.setdefault(
            cell.get("cell_type", "unknown"),
            {"cells": 0, "lines": 0, "characters": 0},
        )
        source = cell_source(cell)
        entry["cells"] += 1
        entry["lines"] += source.count("\n") + 1
        entry["characters"] += len(source)
    return stats


def strip_outputs(notebook: dict) -> str:
    """Clear the outputs of every code cell and re-serialize the notebook."""
    cleaned = {
        key: value for key, value in notebook.items() if key != "cells"
    }
    cleaned["cells"] = [
        {
            **cell,
            **({"outputs": [], "execution_count": None} if cell.get("cell_type") == "code" else {}),
        }
        for cell in notebook.get("cells", [])
    ]
    return json.dumps(cleaned)
