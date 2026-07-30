"""Reference implementations of the workloads exercised by the benchmark suite.

The playground modules at the repository root (`json_to_user.py`,
`convert_comments_to_code.py`) are intentionally left unfinished so that users
can complete them with Copilot during the demo. To keep those exercises intact
while still measuring something real, the same two domains are implemented here
in a self-contained way:

* JSON <-> `User` conversion, mirroring `json_to_user.py`.
* SARIF report aggregation, mirroring the shape of the `snyk_*_results.json`
  artifacts committed at the repository root.

Everything is deterministic: the data generators take an explicit seed so a
benchmark run always measures the exact same amount of work.
"""

from __future__ import annotations

import json
import random
from typing import Any, Iterable

SEVERITIES = ("none", "note", "warning", "error")


class User:
    """Same shape as the `User` class used in the JSONtoUser code tour."""

    __slots__ = ("name", "email", "password")

    def __init__(self, name: str, email: str, password: str) -> None:
        self.name = name
        self.email = email
        self.password = password

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return (
            self.name == other.name
            and self.email == other.email
            and self.password == other.password
        )


def create_user(payload: dict[str, str]) -> User:
    """Build a `User` out of a decoded JSON object."""
    return User(
        name=payload["name"],
        email=payload["email"],
        password=payload["password"],
    )


def jsonify_user(user: User) -> str:
    """Serialize a `User` back to a JSON document."""
    return json.dumps(
        {"name": user.name, "email": user.email, "password": user.password}
    )


def parse_users(raw: str) -> list[User]:
    """Decode a JSON array of user objects into `User` instances."""
    return [create_user(payload) for payload in json.loads(raw)]


def serialize_users(users: Iterable[User]) -> str:
    """Encode `User` instances back into a single JSON array."""
    return json.dumps(
        [
            {"name": user.name, "email": user.email, "password": user.password}
            for user in users
        ]
    )


def roundtrip_users(raw: str) -> str:
    """Full decode/encode cycle, the most common shape in real API handlers."""
    return serialize_users(parse_users(raw))


def make_user_payloads(count: int, *, seed: int = 0) -> list[dict[str, str]]:
    """Generate `count` deterministic user payloads."""
    rng = random.Random(seed)
    payloads = []
    for index in range(count):
        first = f"user{index:06d}"
        payloads.append(
            {
                "name": f"{first.title()} Doe",
                "email": f"{first}@example.com",
                "password": f"password{rng.randrange(10**8):08d}",
            }
        )
    return payloads


def make_users_json(count: int, *, seed: int = 0) -> str:
    """Serialized JSON array of `count` user payloads."""
    return json.dumps(make_user_payloads(count, seed=seed))


def make_sarif_report(
    finding_count: int, *, rule_count: int = 32, seed: int = 0
) -> str:
    """Generate a SARIF document shaped like `snyk_code_results.json`.

    The committed Snyk artifacts have empty `results` arrays (the scan found
    nothing), so a scaled-up document with the same schema is generated here to
    exercise the aggregation code with a realistic amount of data.
    """
    rng = random.Random(seed)
    rules = [
        {
            "id": f"python/Rule{index:03d}",
            "name": f"Rule{index:03d}",
            "shortDescription": {"text": f"Finding class {index}"},
            "defaultConfiguration": {"level": SEVERITIES[index % len(SEVERITIES)]},
            "properties": {
                "tags": ["security", f"category-{index % 7}"],
                "precision": "very-high",
            },
        }
        for index in range(rule_count)
    ]

    results = []
    for index in range(finding_count):
        rule_index = rng.randrange(rule_count)
        start_line = rng.randrange(1, 800)
        results.append(
            {
                "ruleId": rules[rule_index]["id"],
                "ruleIndex": rule_index,
                "level": SEVERITIES[rng.randrange(len(SEVERITIES))],
                "message": {"text": f"Potential issue #{index} detected"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": f"src/module_{index % 64}.py",
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": start_line,
                                "endLine": start_line + rng.randrange(0, 4),
                                "startColumn": rng.randrange(1, 40),
                                "endColumn": rng.randrange(40, 90),
                            },
                        }
                    }
                ],
                "properties": {"priorityScore": rng.randrange(0, 1000)},
            }
        )

    return json.dumps(
        {
            "$schema": (
                "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/"
                "schemas/sarif-schema-2.1.0.json"
            ),
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SnykCode",
                            "semanticVersion": "1.1304.0",
                            "version": "1.1304.0",
                            "informationUri": "https://docs.snyk.io/",
                            "rules": rules,
                        }
                    },
                    "results": results,
                    "properties": {
                        "coverage": [
                            {
                                "files": 64,
                                "isSupported": True,
                                "lang": ".py",
                                "type": "SUPPORTED",
                            }
                        ]
                    },
                    "automationDetails": {"id": "Snyk/Code/benchmark"},
                }
            ],
        }
    )


def parse_sarif(raw: str) -> dict[str, Any]:
    """Decode a SARIF document."""
    return json.loads(raw)


def extract_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a SARIF document into one record per finding."""
    findings = []
    for run in report.get("runs", []):
        rules = run.get("tool", {}).get("driver", {}).get("rules", [])
        for result in run.get("results", []):
            rule_index = result.get("ruleIndex")
            rule = rules[rule_index] if isinstance(rule_index, int) else {}
            level = result.get("level") or (
                rule.get("defaultConfiguration", {}).get("level", "none")
            )
            for location in result.get("locations", []):
                physical = location.get("physicalLocation", {})
                findings.append(
                    {
                        "rule_id": result.get("ruleId", ""),
                        "level": level,
                        "path": physical.get("artifactLocation", {}).get("uri", ""),
                        "line": physical.get("region", {}).get("startLine", 0),
                        "score": result.get("properties", {}).get("priorityScore", 0),
                        "tags": tuple(rule.get("properties", {}).get("tags", ())),
                    }
                )
    return findings


def summarize_findings(findings: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate findings by level, rule, file and tag."""
    by_level: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    by_file: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    total_score = 0
    count = 0

    for finding in findings:
        count += 1
        total_score += finding["score"]
        by_level[finding["level"]] = by_level.get(finding["level"], 0) + 1
        by_rule[finding["rule_id"]] = by_rule.get(finding["rule_id"], 0) + 1
        by_file[finding["path"]] = by_file.get(finding["path"], 0) + 1
        for tag in finding["tags"]:
            by_tag[tag] = by_tag.get(tag, 0) + 1

    worst_files = sorted(by_file.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "total": count,
        "average_score": (total_score / count) if count else 0.0,
        "by_level": by_level,
        "by_rule": by_rule,
        "by_tag": by_tag,
        "worst_files": worst_files,
    }


def analyze_sarif(raw: str) -> dict[str, Any]:
    """End-to-end pipeline: decode, flatten, then aggregate."""
    return summarize_findings(extract_findings(parse_sarif(raw)))
