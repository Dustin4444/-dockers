"""Benchmarks for the JSON <-> `User` conversion workload."""

from __future__ import annotations

import pytest

from benchmarks.workloads import (
    create_user,
    jsonify_user,
    make_user_payloads,
    make_users_json,
    parse_users,
    roundtrip_users,
    serialize_users,
)

SIZES = (10, 1_000, 20_000)


@pytest.mark.benchmark
def test_create_user_single() -> None:
    payload = make_user_payloads(1)[0]
    create_user(payload)


@pytest.mark.benchmark
def test_jsonify_user_single() -> None:
    user = create_user(make_user_payloads(1)[0])
    jsonify_user(user)


@pytest.mark.parametrize("size", SIZES)
def test_parse_users(benchmark, size: int) -> None:
    raw = make_users_json(size)
    users = benchmark(parse_users, raw)
    assert len(users) == size


@pytest.mark.parametrize("size", SIZES)
def test_serialize_users(benchmark, size: int) -> None:
    users = [create_user(payload) for payload in make_user_payloads(size)]
    raw = benchmark(serialize_users, users)
    assert raw.startswith("[")


@pytest.mark.parametrize("size", SIZES)
def test_roundtrip_users(benchmark, size: int) -> None:
    raw = make_users_json(size)
    result = benchmark(roundtrip_users, raw)
    assert parse_users(result) == parse_users(raw)
