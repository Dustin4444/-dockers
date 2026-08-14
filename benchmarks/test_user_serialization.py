"""Benchmarks for the JSON <-> ``User`` conversion workload."""

from __future__ import annotations

import json

import pytest

from workloads import (
    create_user,
    dump_users,
    jsonify_user,
    load_users,
    make_user_payloads,
)


@pytest.mark.benchmark
def test_create_single_user() -> None:
    payload = make_user_payloads(1)[0]
    for _ in range(1000):
        create_user(payload)


@pytest.mark.benchmark
def test_jsonify_single_user() -> None:
    user = create_user(make_user_payloads(1)[0])
    for _ in range(1000):
        jsonify_user(user)


@pytest.mark.parametrize("count", [100, 10_000])
def test_load_users(benchmark, count: int) -> None:
    raw = json.dumps(make_user_payloads(count))
    users = benchmark(load_users, raw)
    assert len(users) == count


@pytest.mark.parametrize("count", [100, 10_000])
def test_dump_users(benchmark, count: int) -> None:
    users = [create_user(payload) for payload in make_user_payloads(count)]
    raw = benchmark(dump_users, users)
    assert raw.startswith("[")


def test_users_roundtrip(benchmark) -> None:
    raw = json.dumps(make_user_payloads(2_000))

    def roundtrip() -> str:
        return dump_users(load_users(raw))

    assert len(json.loads(benchmark(roundtrip))) == 2_000
