# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Tests for the `BatchUnrollReceiver`."""

from unittest.mock import MagicMock

from frequenz.channels import Receiver

from frequenz.client.reporting._batch_unroll_receiver import BatchUnrollReceiver


def test_close_closes_stream() -> None:
    """Closing the receiver closes the underlying stream."""
    stream = MagicMock(spec=Receiver)

    BatchUnrollReceiver(stream).close()

    stream.close.assert_called_once_with()
