# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Client for requests to the Reporting API."""

from collections import abc, namedtuple
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterable, cast

# pylint: disable=no-name-in-module
from frequenz.api.common.v1.microgrid.microgrid_pb2 import (
    MicrogridComponentIDs as PBMicrogridComponentIDs,
)
from frequenz.api.common.v1.microgrid.microgrid_pb2 import (
    MicrogridSensorIDs as PBMicrogridSensorIDs,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    AggregationConfig as PBAggregationConfig,
)
from frequenz.api.reporting.v1.reporting_pb2 import FilterOption as PBFilterOption
from frequenz.api.reporting.v1.reporting_pb2 import (
    MetricConnections as PBMetricConnections,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveAggregatedMicrogridComponentsDataStreamRequest as PBAggregatedStreamRequest,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveAggregatedMicrogridComponentsDataStreamResponse as PBAggregatedStreamResponse,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveMicrogridComponentsDataStreamRequest as PBReceiveMicrogridComponentsDataStreamRequest,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveMicrogridComponentsDataStreamResponse as PBReceiveMicrogridComponentsDataStreamResponse,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveMicrogridSensorsDataStreamRequest as PBReceiveMicrogridSensorsDataStreamRequest,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ReceiveMicrogridSensorsDataStreamResponse as PBReceiveMicrogridSensorsDataStreamResponse,
)
from frequenz.api.reporting.v1.reporting_pb2 import (
    ResamplingOptions as PBResamplingOptions,
)
from frequenz.api.reporting.v1.reporting_pb2 import TimeFilter as PBTimeFilter
from frequenz.api.reporting.v1.reporting_pb2_grpc import ReportingStub
from frequenz.client.base.channel import ChannelOptions
from frequenz.client.base.client import BaseApiClient
from frequenz.client.base.exception import ClientNotConnected
from frequenz.client.base.streaming import GrpcStreamBroadcaster
from frequenz.client.common.metric import Metric
from google.protobuf.timestamp_pb2 import Timestamp as PBTimestamp

MetricSample = namedtuple(
    "MetricSample", ["timestamp", "microgrid_id", "component_id", "metric", "value"]
)
"""Type for a sample of a time series incl. metric type, microgrid and component ID

A named tuple was chosen to allow safe access to the fields while keeping the
simplicity of a tuple. This data type can be easily used to create a numpy array
or a pandas DataFrame.
"""


@dataclass(frozen=True)
class GenericDataBatch:
    """Base class for batches of microgrid data (components or sensors).

    This class serves as a base for handling batches of data related to microgrid
    components or sensors. It manages the received protocol buffer (PB) data,
    provides access to relevant items via specific attributes, and includes
    functionality to work with bounds if applicable.
    """

    _data_pb: Any
    id_attr: str
    items_attr: str
    has_bounds: bool = False

    def is_empty(self) -> bool:
        """Check if the batch contains valid data.

        Returns:
            True if the batch contains no valid data.
        """
        items = getattr(self._data_pb, self.items_attr, [])
        if not items:
            return True
        for item in items:
            if not getattr(item, "metric_samples", []) and not getattr(
                item, "states", []
            ):
                return True
        return False

    def __iter__(self) -> Iterator[MetricSample]:
        """Get generator that iterates over all values in the batch.

        Note: So far only `SimpleMetricSample` in the `MetricSampleVariant`
        message is supported.


        Yields:
            A named tuple with the following fields:
            * timestamp: The timestamp of the metric sample.
            * microgrid_id: The microgrid ID.
            * component_id: The component ID.
            * metric: The metric name.
            * value: The metric value.
        """
        mid = self._data_pb.microgrid_id
        items = getattr(self._data_pb, self.items_attr)

        for item in items:
            cid = getattr(item, self.id_attr)
            for sample in getattr(item, "metric_samples", []):
                ts = sample.sampled_at.ToDatetime().replace(tzinfo=timezone.utc)
                met = Metric.from_proto(sample.metric).name
                value = (
                    sample.value.simple_metric.value
                    if sample.value.HasField("simple_metric")
                    else None
                )
                yield MetricSample(ts, mid, cid, met, value)

                if self.has_bounds:
                    for i, bound in enumerate(sample.bounds):
                        if bound.lower:
                            yield MetricSample(
                                ts, mid, cid, f"{met}_bound_{i}_lower", bound.lower
                            )
                        if bound.upper:
                            yield MetricSample(
                                ts, mid, cid, f"{met}_bound_{i}_upper", bound.upper
                            )

            for state in getattr(item, "states", []):
                ts = state.sampled_at.ToDatetime().replace(tzinfo=timezone.utc)
                for name, category in {
                    "state": getattr(state, "states", []),
                    "warning": getattr(state, "warnings", []),
                    "error": getattr(state, "errors", []),
                }.items():
                    if not isinstance(category, abc.Iterable):
                        continue
                    for s in category:
                        yield MetricSample(ts, mid, cid, name, s)


@dataclass(frozen=True)
class ComponentsDataBatch(GenericDataBatch):
    """Batch of microgrid components data."""

    def __init__(self, data_pb: PBReceiveMicrogridComponentsDataStreamResponse):
        """Initialize the ComponentsDataBatch.

        Args:
            data_pb: The underlying protobuf message.
        """
        super().__init__(
            data_pb, id_attr="component_id", items_attr="components", has_bounds=True
        )


@dataclass(frozen=True)
class SensorsDataBatch(GenericDataBatch):
    """Batch of microgrid sensors data."""

    def __init__(self, data_pb: PBReceiveMicrogridSensorsDataStreamResponse):
        """Initialize the SensorsDataBatch.

        Args:
            data_pb: The underlying protobuf message.
        """
        super().__init__(data_pb, id_attr="sensor_id", items_attr="sensors")


@dataclass(frozen=True)
class AggregatedMetric:
    """An aggregated metric sample returned by the Reporting service."""

    _data_pb: PBAggregatedStreamResponse
    """The underlying protobuf message."""

    def sample(self) -> MetricSample:
        """Return the aggregated metric sample."""
        return MetricSample(
            timestamp=self._data_pb.sample.sampled_at.ToDatetime().replace(
                tzinfo=timezone.utc
            ),
            microgrid_id=self._data_pb.aggregation_config.microgrid_id,
            component_id=self._data_pb.aggregation_config.aggregation_formula,
            metric=self._data_pb.aggregation_config.metric,
            value=self._data_pb.sample.sample.value,
        )


class ReportingApiClient(BaseApiClient[ReportingStub]):
    """A client for the Reporting service."""

    def __init__(
        self,
        server_url: str,
        key: str | None = None,
        connect: bool = True,
        channel_defaults: ChannelOptions = ChannelOptions(),  # default options
    ) -> None:
        """Create a new Reporting client.

        Args:
            server_url: The URL of the Reporting service.
            key: The API key for the authorization.
            connect: Whether to connect to the server immediately.
            channel_defaults: The default channel options.
        """
        super().__init__(
            server_url,
            ReportingStub,
            connect=connect,
            channel_defaults=channel_defaults,
        )

        self._broadcasters: dict[int, GrpcStreamBroadcaster[Any, Any]] = {}

        self._metadata = (("key", key),) if key else ()

    @property
    def stub(self) -> ReportingStub:
        """The gRPC stub for the API."""
        if self.channel is None or self._stub is None:
            raise ClientNotConnected(server_url=self.server_url, operation="stub")
        return self._stub

    # pylint: disable=too-many-arguments
    async def list_single_component_data(
        self,
        *,
        microgrid_id: int,
        component_id: int,
        metrics: Metric | list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
        include_bounds: bool = False,
    ) -> AsyncIterator[MetricSample]:
        """Iterate over the data for a single metric.

        Args:
            microgrid_id: The microgrid ID.
            component_id: The component ID.
            metrics: The metric name or list of metric names.
            start_dt: start datetime, if None, the earliest available data will be used
            end_dt: end datetime, if None starts streaming indefinitely from start_dt
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.
            include_bounds: Whether to include the bound data.

        Yields:
            A named tuple with the following fields:
            * timestamp: The timestamp of the metric sample.
            * value: The metric value.
        """
        async for batch in self._list_microgrid_components_data_batch(
            microgrid_components=[(microgrid_id, [component_id])],
            metrics=[metrics] if isinstance(metrics, Metric) else metrics,
            start_dt=start_dt,
            end_dt=end_dt,
            resampling_period=resampling_period,
            include_states=include_states,
            include_bounds=include_bounds,
        ):
            for entry in batch:
                yield entry

    # pylint: disable=too-many-arguments
    async def list_microgrid_components_data(
        self,
        *,
        microgrid_components: list[tuple[int, list[int]]],
        metrics: Metric | list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
        include_bounds: bool = False,
    ) -> AsyncIterator[MetricSample]:
        """Iterate over the data for multiple microgrids and components.

        Args:
            microgrid_components: List of tuples where each tuple contains
                                  microgrid ID and corresponding component IDs.
            metrics: The metric name or list of metric names.
            start_dt: start datetime, if None, the earliest available data will be used
            end_dt: end datetime, if None starts streaming indefinitely from start_dt
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.
            include_bounds: Whether to include the bound data.

        Yields:
            A named tuple with the following fields:
            * microgrid_id: The microgrid ID.
            * component_id: The component ID.
            * metric: The metric name.
            * timestamp: The timestamp of the metric sample.
            * value: The metric value.
        """
        async for batch in self._list_microgrid_components_data_batch(
            microgrid_components=microgrid_components,
            metrics=[metrics] if isinstance(metrics, Metric) else metrics,
            start_dt=start_dt,
            end_dt=end_dt,
            resampling_period=resampling_period,
            include_states=include_states,
            include_bounds=include_bounds,
        ):
            for entry in batch:
                yield entry

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    async def _list_microgrid_components_data_batch(
        self,
        *,
        microgrid_components: list[tuple[int, list[int]]],
        metrics: list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
        include_bounds: bool = False,
    ) -> AsyncIterator[ComponentsDataBatch]:
        """Iterate over the component data batches in the stream using GrpcStreamBroadcaster.

        Args:
            microgrid_components: A list of tuples of microgrid IDs and component IDs.
            metrics: A list of metrics.
            start_dt: start datetime, if None, the earliest available data will be used
            end_dt: end datetime, if None starts streaming indefinitely from start_dt
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.
            include_bounds: Whether to include the bound data.

        Yields:
            A ComponentsDataBatch object of microgrid components data.
        """
        microgrid_components_pb = [
            PBMicrogridComponentIDs(microgrid_id=mid, component_ids=cids)
            for mid, cids in microgrid_components
        ]

        def dt2ts(dt: datetime) -> PBTimestamp:
            ts = PBTimestamp()
            ts.FromDatetime(dt)
            return ts

        time_filter = PBTimeFilter(
            start=dt2ts(start_dt) if start_dt else None,
            end=dt2ts(end_dt) if end_dt else None,
        )

        incl_states = (
            PBFilterOption.FILTER_OPTION_INCLUDE
            if include_states
            else PBFilterOption.FILTER_OPTION_EXCLUDE
        )
        incl_bounds = (
            PBFilterOption.FILTER_OPTION_INCLUDE
            if include_bounds
            else PBFilterOption.FILTER_OPTION_EXCLUDE
        )
        include_options = PBReceiveMicrogridComponentsDataStreamRequest.IncludeOptions(
            bounds=incl_bounds,
            states=incl_states,
        )

        stream_filter = PBReceiveMicrogridComponentsDataStreamRequest.StreamFilter(
            time_filter=time_filter,
            resampling_options=PBResamplingOptions(
                resolution=(
                    round(resampling_period.total_seconds())
                    if resampling_period is not None
                    else None
                )
            ),
            include_options=include_options,
        )

        metric_conns_pb = [
            PBMetricConnections(
                metric=metric.to_proto(),
                connections=[],
            )
            for metric in metrics
        ]

        request = PBReceiveMicrogridComponentsDataStreamRequest(
            microgrid_components=microgrid_components_pb,
            metrics=metric_conns_pb,
            filter=stream_filter,
        )

        def transform_response(
            response: PBReceiveMicrogridComponentsDataStreamResponse,
        ) -> ComponentsDataBatch:
            return ComponentsDataBatch(response)

        async def stream_method() -> (
            AsyncIterable[PBReceiveMicrogridComponentsDataStreamResponse]
        ):
            call_iterator = self.stub.ReceiveMicrogridComponentsDataStream(
                request, metadata=self._metadata
            )
            async for response in cast(
                AsyncIterable[PBReceiveMicrogridComponentsDataStreamResponse],
                call_iterator,
            ):
                yield response

        broadcaster = GrpcStreamBroadcaster(
            stream_name="microgrid-components-data-stream",
            stream_method=stream_method,
            transform=transform_response,
            retry_strategy=None,
        )

        receiver = broadcaster.new_receiver()
        async for data in receiver:
            yield data

    # pylint: disable=too-many-arguments
    async def receive_single_sensor_data(
        self,
        *,
        microgrid_id: int,
        sensor_id: int,
        metrics: Metric | list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
    ) -> AsyncIterator[MetricSample]:
        """Iterate over the data for a single sensor and metric.

        Args:
            microgrid_id: The microgrid ID.
            sensor_id: The sensor ID.
            metrics: The metric name or list of metric names.
            start_dt: start datetime, if None, the earliest available data will be used.
            end_dt: end datetime, if None starts streaming indefinitely from start_dt.
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.

        Yields:
            A named tuple with the following fields:
            * timestamp: The timestamp of the metric sample.
            * value: The metric value.
        """
        receiver = await self._receive_microgrid_sensors_data_batch(
            microgrid_sensors=[(microgrid_id, [sensor_id])],
            metrics=[metrics] if isinstance(metrics, Metric) else metrics,
            start_dt=start_dt,
            end_dt=end_dt,
            resampling_period=resampling_period,
            include_states=include_states,
        )
        async for batch in receiver:
            for entry in batch:
                yield entry

    # pylint: disable=too-many-arguments
    async def receive_microgrid_sensors_data(
        self,
        *,
        microgrid_sensors: list[tuple[int, list[int]]],
        metrics: Metric | list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
    ) -> AsyncIterator[MetricSample]:
        """Iterate over the data for multiple sensors in a microgrid.

        Args:
            microgrid_sensors: List of tuples where each tuple contains
                                microgrid ID and corresponding sensor IDs.
            metrics: The metric name or list of metric names.
            start_dt: start datetime, if None, the earliest available data will be used.
            end_dt: end datetime, if None starts streaming indefinitely from start_dt.
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.

        Yields:
            A named tuple with the following fields:
            * microgrid_id: The microgrid ID.
            * sensor_id: The sensor ID.
            * metric: The metric name.
            * timestamp: The timestamp of the metric sample.
            * value: The metric value.
        """
        receiver = await self._receive_microgrid_sensors_data_batch(
            microgrid_sensors=microgrid_sensors,
            metrics=[metrics] if isinstance(metrics, Metric) else metrics,
            start_dt=start_dt,
            end_dt=end_dt,
            resampling_period=resampling_period,
            include_states=include_states,
        )
        async for batch in receiver:
            for entry in batch:
                yield entry

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    async def _receive_microgrid_sensors_data_batch(
        self,
        *,
        microgrid_sensors: list[tuple[int, list[int]]],
        metrics: list[Metric],
        start_dt: datetime | None,
        end_dt: datetime | None,
        resampling_period: timedelta | None,
        include_states: bool = False,
    ) -> AsyncIterator[SensorsDataBatch]:
        """Iterate over the sensor data batches in the stream using GrpcStreamBroadcaster.

        Args:
            microgrid_sensors: A list of tuples of microgrid IDs and sensor IDs.
            metrics: A list of metrics.
            start_dt: start datetime, if None, the earliest available data will be used.
            end_dt: end datetime, if None starts streaming indefinitely from start_dt.
            resampling_period: The period for resampling the data.
            include_states: Whether to include the state data.

        Returns:
            A SensorDataBatch object of microgrid sensors data.
        """
        microgrid_sensors_pb = [
            PBMicrogridSensorIDs(microgrid_id=mid, sensor_ids=sids)
            for mid, sids in microgrid_sensors
        ]

        def dt2ts(dt: datetime) -> PBTimestamp:
            ts = PBTimestamp()
            ts.FromDatetime(dt)
            return ts

        time_filter = PBTimeFilter(
            start=dt2ts(start_dt) if start_dt else None,
            end=dt2ts(end_dt) if end_dt else None,
        )

        incl_states = (
            PBFilterOption.FILTER_OPTION_INCLUDE
            if include_states
            else PBFilterOption.FILTER_OPTION_EXCLUDE
        )
        include_options = PBReceiveMicrogridSensorsDataStreamRequest.IncludeOptions(
            states=incl_states,
        )

        stream_filter = PBReceiveMicrogridSensorsDataStreamRequest.StreamFilter(
            time_filter=time_filter,
            resampling_options=PBResamplingOptions(
                resolution=(
                    round(resampling_period.total_seconds())
                    if resampling_period is not None
                    else None
                )
            ),
            include_options=include_options,
        )

        metric_conns_pb = [
            PBMetricConnections(
                metric=metric.to_proto(),
                connections=[],
            )
            for metric in metrics
        ]

        request = PBReceiveMicrogridSensorsDataStreamRequest(
            microgrid_sensors=microgrid_sensors_pb,
            metrics=metric_conns_pb,
            filter=stream_filter,
        )

        def transform_response(
            response: PBReceiveMicrogridSensorsDataStreamResponse,
        ) -> SensorsDataBatch:
            return SensorsDataBatch(response)

        async def stream_method() -> (
            AsyncIterable[PBReceiveMicrogridSensorsDataStreamResponse]
        ):
            call_iterator = self.stub.ReceiveMicrogridSensorsDataStream(
                request, metadata=self._metadata
            )
            async for response in cast(
                AsyncIterable[PBReceiveMicrogridSensorsDataStreamResponse],
                call_iterator,
            ):
                yield response

        broadcaster = GrpcStreamBroadcaster(
            stream_name="microgrid-sensors-data-stream",
            stream_method=stream_method,
            transform=transform_response,
            retry_strategy=None,
        )

        return broadcaster.new_receiver()

    async def receive_aggregated_data(
        self,
        *,
        microgrid_id: int,
        metric: Metric,
        aggregation_formula: str,
        start: datetime | None,
        end: datetime | None,
        resampling_period: timedelta,
    ) -> AsyncIterator[MetricSample]:
        """Iterate over aggregated data for a single metric using GrpcStreamBroadcaster.

        For now this only supports a single metric and aggregation formula.
        Args:
            microgrid_id: The microgrid ID.
            metric: The metric name.
            aggregation_formula: The aggregation formula.
            start: start datetime, if None, the earliest available data will be used
            end: end datetime, if None starts streaming indefinitely from start
            resampling_period: The period for resampling the data.

        Yields:
            An iterator over the aggregated metric samples.

        Raises:
            ValueError: If the resampling_period is not provided.
        """
        if not resampling_period:
            raise ValueError("resampling_period must be provided")

        aggregation_config = PBAggregationConfig(
            microgrid_id=microgrid_id,
            metric=metric.to_proto(),
            aggregation_formula=aggregation_formula,
        )

        def dt2ts(dt: datetime) -> PBTimestamp:
            ts = PBTimestamp()
            ts.FromDatetime(dt)
            return ts

        time_filter = PBTimeFilter(
            start=dt2ts(start) if start else None,
            end=dt2ts(end) if end else None,
        )

        stream_filter = PBAggregatedStreamRequest.AggregationStreamFilter(
            time_filter=time_filter,
            resampling_options=PBResamplingOptions(
                resolution=round(resampling_period.total_seconds())
            ),
        )

        request = PBAggregatedStreamRequest(
            aggregation_configs=[aggregation_config],
            filter=stream_filter,
        )

        def transform_response(response: PBAggregatedStreamResponse) -> MetricSample:
            return AggregatedMetric(response).sample()

        async def stream_method() -> AsyncIterable[PBAggregatedStreamResponse]:
            call_iterator = self.stub.ReceiveAggregatedMicrogridComponentsDataStream(
                request, metadata=self._metadata
            )

            async for response in cast(
                AsyncIterable[PBAggregatedStreamResponse], call_iterator
            ):
                yield response

        broadcaster = GrpcStreamBroadcaster(
            stream_name="aggregated-microgrid-data-stream",
            stream_method=stream_method,
            transform=transform_response,
            retry_strategy=None,
        )

        receiver = broadcaster.new_receiver()
        async for data in receiver:
            yield data
