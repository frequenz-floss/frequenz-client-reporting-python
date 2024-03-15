# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.client.reporting package."""
import pytest

from frequenz.client.reporting import delete_me


def test_client_reporting_succeeds() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function succeeds."""
    assert delete_me() is True


def test_client_reporting_fails() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function fails."""
    with pytest.raises(RuntimeError, match="This function should be removed!"):
        delete_me(blow_up=True)
