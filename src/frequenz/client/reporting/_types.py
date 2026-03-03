# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Types for the Reporting API client."""

import math
from collections.abc import Iterator, MutableSequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Generic, NamedTuple, Protocol, TypeVar, cast

# pylint: disable=no-name-in-module
from frequenz.api.common.v1alpha8.metrics.metrics_pb2 import (
    MetricSample as PbMetricSample,
)
from frequenz.api.common.v1alpha8.microgrid.electrical_components.electrical_components_pb2 import (
    ElectricalComponentDiagnostic as PbElectricalComponentDiagnostic,
)
from frequenz.api.common.v1alpha8.microgrid.electrical_components.electrical_components_pb2 import (
    ElectricalComponentStateCode as PbElectricalComponentStateCode,
)
from frequenz.api.common.v1alpha8.microgrid.electrical_components.electrical_components_pb2 import (
    ElectricalComponentStateSnapshot as PbElectricalComponentStateSnapshot,
)
from frequenz.api.common.v1alpha8.microgrid.electrical_components.electrical_components_pb2 import (
    ElectricalComponentTelemetry as PbElectricalComponentTelemetry,
)
from frequenz.api.common.v1alpha8.microgrid.sensors.sensors_pb2 import (
    SensorDiagnostic as PbSensorDiagnostic,
)
from frequenz.api.common.v1alpha8.microgrid.sensors.sensors_pb2 import (
    SensorStateCode as PbSensorStateCode,
)
from frequenz.api.common.v1alpha8.microgrid.sensors.sensors_pb2 import (
    SensorStateSnapshot as PbSensorStateSnapshot,
)
from frequenz.api.common.v1alpha8.microgrid.sensors.sensors_pb2 import (
    SensorTelemetry as PbSensorTelemetry,
)
from frequenz.api.reporting.v1alpha10.reporting_pb2 import (
    ReceiveAggregatedMicrogridComponentsDataStreamResponse as PBAggregatedStreamResponse,
)
from frequenz.api.reporting.v1alpha10.reporting_pb2 import (
    ReceiveMicrogridComponentsDataStreamResponse as PBReceiveMicrogridComponentsDataStreamResponse,
)
from frequenz.api.reporting.v1alpha10.reporting_pb2 import (
    ReceiveMicrogridSensorsDataStreamResponse as PBReceiveMicrogridSensorsDataStreamResponse,
)

# pylint: enable=no-name-in-module
from frequenz.client.common.metrics import Metric
from frequenz.client.common.proto import datetime_from_proto, enum_from_proto


class MetricSample(NamedTuple):
    """Type for a sample of a time series incl. metric type, microgrid and component ID.

    A named tuple was chosen to allow safe access to the fields while keeping the
    simplicity of a tuple. This data type can be easily used to create a numpy array
    or a pandas DataFrame.
    """

    timestamp: datetime
    microgrid_id: int
    component_id: int | str
    metric: str
    value: (
        float
        | PbElectricalComponentStateCode.ValueType
        | PbSensorStateCode.ValueType
        | PbElectricalComponentDiagnostic
        | PbSensorDiagnostic
    )


class _PbMicrogridTelem(Protocol):
    """Protocol for microgrid telemetry from the Reporting API client."""

    @property
    def microgrid_id(self) -> int:
        """Return the microgrid ID of the telemetry batch."""


class _PbComponentTelem(Protocol):
    """Protocol for telemetry items in the Reporting API client."""

    @property
    def metric_samples(self) -> MutableSequence[PbMetricSample]:
        """Return the metric samples of the telemetry item."""

    @property
    def state_snapshots(self) -> MutableSequence[Any]:
        """List of state snapshots associated with this telemetry item."""


_MicrogridTelemT = TypeVar("_MicrogridTelemT", bound=_PbMicrogridTelem)
_ComponentTelemT = TypeVar("_ComponentTelemT", bound=_PbComponentTelem)
_StateSnapshotT = TypeVar(
    "_StateSnapshotT", bound=PbElectricalComponentStateSnapshot | PbSensorStateSnapshot
)


@dataclass(frozen=True)
class GenericDataBatch(Generic[_MicrogridTelemT, _ComponentTelemT, _StateSnapshotT]):
    """Base class for batches of microgrid data (components or sensors).

    This class serves as a base for handling batches of data related to microgrid
    components or sensors. It manages the received protocol buffer (PB) data,
    provides access to relevant items via specific attributes, and includes
    functionality to work with bounds if applicable.
    """

    _data_pb: _MicrogridTelemT
    id_fetcher: Callable[[_ComponentTelemT], int]
    items_fetcher: Callable[[_MicrogridTelemT], MutableSequence[_ComponentTelemT]]
    has_bounds: bool = False

    def is_empty(self) -> bool:
        """Check if the batch contains valid data.

        Returns:
            True if the batch contains no valid data.
        """
        items = self.items_fetcher(self._data_pb)
        if not items:
            return True
        for item in items:
            if item.metric_samples or item.state_snapshots:
                return False
        return True

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    def __iter__(self) -> Iterator[MetricSample]:
        """Get generator that iterates over all values in the batch.

        `SimpleMetricSample` and `AggregatedMetricSample` in the
        `MetricSampleVariant` message is supported.


        Yields:
            A named tuple with the following fields:
            * timestamp: The timestamp of the metric sample.
            * microgrid_id: The microgrid ID.
            * component_id: The component ID.
            * metric: The metric name.
            * value: The metric value.
        """
        mid = self._data_pb.microgrid_id
        items = self.items_fetcher(self._data_pb)

        for item in items:
            cid = self.id_fetcher(item)
            for sample in item.metric_samples:
                ts = datetime_from_proto(sample.sample_time)
                met = enum_from_proto(sample.metric, Metric, allow_invalid=False).name

                # Handle simple_metric
                if sample.value.HasField("simple_metric"):
                    value = sample.value.simple_metric.value
                    yield MetricSample(ts, mid, cid, met, value)

                # Handle aggregated_metric
                if sample.value.HasField("aggregated_metric"):
                    agg = sample.value.aggregated_metric
                    # Average value
                    yield MetricSample(ts, mid, cid, f"{met}_avg", agg.avg_value)
                    # Min value if present
                    if agg.HasField("min_value"):
                        yield MetricSample(ts, mid, cid, f"{met}_min", agg.min_value)
                    # Max value if present
                    if agg.HasField("max_value"):
                        yield MetricSample(ts, mid, cid, f"{met}_max", agg.max_value)
                    # Optionally yield individual raw values
                    for i, raw in enumerate(agg.raw_values):
                        yield MetricSample(ts, mid, cid, f"{met}_raw_{i}", raw)

                if self.has_bounds:
                    for i, bound in enumerate(sample.bounds):
                        lower = bound.lower if bound.HasField("lower") else -math.inf
                        yield MetricSample(
                            ts, mid, cid, f"{met}_bound_{i}_lower", lower
                        )
                        upper = bound.upper if bound.HasField("upper") else math.inf
                        yield MetricSample(
                            ts, mid, cid, f"{met}_bound_{i}_upper", upper
                        )

            for state in item.state_snapshots:
                state = cast(_StateSnapshotT, state)
                ts = datetime_from_proto(state.origin_time)
                for category, category_items in {
                    "state": state.states,
                    "warning": state.warnings,
                    "error": state.errors,
                }.items():
                    for s in category_items:
                        yield MetricSample(ts, mid, cid, category, s)


@dataclass(frozen=True)
class ComponentsDataBatch(
    GenericDataBatch[
        PBReceiveMicrogridComponentsDataStreamResponse,
        PbElectricalComponentTelemetry,
        PbElectricalComponentStateSnapshot,
    ]
):
    """Batch of microgrid components data."""

    def __init__(self, data_pb: PBReceiveMicrogridComponentsDataStreamResponse):
        """Initialize the ComponentsDataBatch.

        Args:
            data_pb: The underlying protobuf message.
        """
        super().__init__(
            data_pb,
            id_fetcher=lambda item: item.electrical_component_id,
            items_fetcher=lambda pb: pb.components,
            has_bounds=True,
        )


@dataclass(frozen=True)
class SensorsDataBatch(
    GenericDataBatch[
        PBReceiveMicrogridSensorsDataStreamResponse,
        PbSensorTelemetry,
        PbSensorStateSnapshot,
    ]
):
    """Batch of microgrid sensors data."""

    def __init__(self, data_pb: PBReceiveMicrogridSensorsDataStreamResponse):
        """Initialize the SensorsDataBatch.

        Args:
            data_pb: The underlying protobuf message.
        """
        super().__init__(
            data_pb,
            id_fetcher=lambda item: item.sensor_id,
            items_fetcher=lambda pb: pb.sensors,
        )


@dataclass(frozen=True)
class AggregatedMetric:
    """An aggregated metric sample returned by the Reporting service."""

    _data_pb: PBAggregatedStreamResponse
    """The underlying protobuf message."""

    def sample(self) -> MetricSample:
        """Return the aggregated metric sample."""
        config = self._data_pb.aggregation_config
        sample = self._data_pb.sample

        timestamp = datetime_from_proto(sample.sample_time)
        microgrid_id = config.microgrid_id
        component_id = config.aggregation_formula
        metric = Metric(config.metric).name
        # Ignoring this verification results in
        # values of zero if the field is not set.
        if sample.HasField("sample"):
            value = sample.sample.value
        else:
            value = math.nan

        ret = MetricSample(
            timestamp=timestamp,
            microgrid_id=microgrid_id,
            component_id=component_id,
            metric=metric,
            value=value,
        )
        return ret
