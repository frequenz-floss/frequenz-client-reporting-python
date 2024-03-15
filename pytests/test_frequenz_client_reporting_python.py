# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.client.reporting package."""


def test_package_import() -> None:
    """Test that the package can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api import frequenz_client_reporting_python

    assert frequenz_client_reporting_python is not None


def test_module_import_components() -> None:
    """Test that the modules can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api.frequenz_client_reporting_python import frequenz_client_reporting_python_pb2

    assert frequenz_client_reporting_python_pb2 is not None

    # pylint: disable=import-outside-toplevel
    from frequenz.api.frequenz_client_reporting_python import frequenz_client_reporting_python_pb2_grpc

    assert frequenz_client_reporting_python_pb2_grpc is not None
