# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.client.reporting package."""
from unittest.mock import MagicMock, patch

import pytest
from frequenz.api.reporting.v1alpha10.reporting_pb2_grpc import ReportingStub
from frequenz.client.base.channel import ChannelOptions
from frequenz.client.base.client import BaseApiClient

from frequenz.client.reporting import ReportingApiClient
from frequenz.client.reporting._types import ComponentsDataBatch


@pytest.mark.asyncio
async def test_client_initialization() -> None:
    """Test that the client initializes the BaseApiClient."""
    # Parameters for the ReportingApiClient initialization
    server_url = "gprc://localhost:50051"
    key = "some-api-key"
    sign_secret = "hunter2"
    connect = True
    channel_defaults = ChannelOptions()

    with patch.object(BaseApiClient, "__init__", return_value=None) as mock_base_init:
        ReportingApiClient(
            server_url,
            auth_key=key,
            connect=connect,
            channel_defaults=channel_defaults,
            sign_secret=sign_secret,
        )  # noqa: F841
        mock_base_init.assert_called_once_with(
            server_url,
            ReportingStub,
            connect=connect,
            channel_defaults=channel_defaults,
            auth_key=key,
            sign_secret=sign_secret,
        )


def test_components_data_batch_is_empty_true() -> None:
    """Test that the is_empty method returns True when the page is empty."""
    data_pb = MagicMock()
    data_pb.components = []
    batch = ComponentsDataBatch(data_pb=data_pb)
    assert batch.is_empty() is True


def test_components_data_batch_is_empty_false() -> None:
    """Test that the is_empty method returns False when the page is not empty."""
    data_pb = MagicMock()
    data_pb.components = [MagicMock()]
    data_pb.components[0].metric_samples = [MagicMock()]
    batch = ComponentsDataBatch(data_pb=data_pb)
    assert batch.is_empty() is False
