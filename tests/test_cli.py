# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Tests for the reporting CLI."""

from unittest.mock import AsyncMock

import pytest

from frequenz.client.reporting.cli import __main__ as cli

_ARGV = ["reporting-cli", "--mid", "1", "--cid", "1"]


def _run_main(
    monkeypatch: pytest.MonkeyPatch, args: list[str], env: dict[str, str]
) -> AsyncMock:
    """Run `main` with `args` and `env`, returning the mocked `run`."""
    run = AsyncMock()
    monkeypatch.setattr(cli, "run", run)
    monkeypatch.setattr("sys.argv", _ARGV + args)
    for name in ("FREQUENZ_API_KEY", "FREQUENZ_API_SECRET"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    cli.main()
    return run


_FALLBACK_ENV = {
    "FREQUENZ_API_KEY": "fallback-key",
    "FREQUENZ_API_SECRET": "fallback-secret",
}


def test_credentials_fall_back_to_frequenz_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`FREQUENZ_API_*` are used when no credentials are given."""
    run = _run_main(monkeypatch, [], _FALLBACK_ENV)

    assert run.call_args.kwargs["auth_key"] == "fallback-key"
    assert run.call_args.kwargs["sign_secret"] == "fallback-secret"


def test_flags_take_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """`--auth_key` and `--sign_secret` win over `FREQUENZ_API_*`."""
    run = _run_main(
        monkeypatch,
        ["--auth_key", "own-key", "--sign_secret", "own-secret"],
        _FALLBACK_ENV,
    )

    assert run.call_args.kwargs["auth_key"] == "own-key"
    assert run.call_args.kwargs["sign_secret"] == "own-secret"


def test_credentials_are_not_mixed_across_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `--auth_key` is never paired with a `FREQUENZ_API_*` secret."""
    run = _run_main(monkeypatch, ["--auth_key", "own-key"], _FALLBACK_ENV)

    assert run.call_args.kwargs["auth_key"] == "own-key"
    assert run.call_args.kwargs["sign_secret"] is None


def test_secret_without_key_does_not_fall_back(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `--sign_secret` alone is an error, not a mixed pair."""
    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["--sign_secret", "own-secret"], _FALLBACK_ENV)

    assert exc_info.value.code != 0
    assert "auth key" in capsys.readouterr().err
