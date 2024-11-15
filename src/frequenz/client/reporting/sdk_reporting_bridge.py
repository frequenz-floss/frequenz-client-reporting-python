from frequenz.client.reporting import ReportingApiClient
from frequenz.client.common.metric import Metric

from frequenz.channels import Receiver, ReceiverStoppedError
from frequenz.client.reporting._base_types import Sample
from frequenz.client.reporting._quantities import Quantity
from datetime import datetime

class _BatchReceiver(Receiver[Sample[Quantity]]):

    def __init__(self, stream):
        self._stream = stream
        self._batch_iter = None
        self._latest_sample = None
        self._no_more_data = False

    async def ready(self) -> bool:
        # If ready is called multiple times, we should return the same result
        # so we don't loose any data
        if self._latest_sample is not None:
            return True

        while True:
            # If we have a batch iterator, try to get the next sample
            if self._batch_iter is not None:
                try:
                    metric_sample = self._batch_iter.__next__()
                    self._latest_sample = Sample(
                        timestamp=metric_sample.timestamp,
                        value=Quantity(value=metric_sample.value),
                    )
                    return True
                # If the batch is done, set the batch iterator to None
                except StopIteration:
                    self._batch_iter = None

            # If we don't have a batch iterator, try to get the next batch
            try:
                batch = await anext(self._stream)
                self._batch_iter = batch.__iter__()
            # If the stream is done, return False
            except StopAsyncIteration:
                self._no_more_data = True
                return False

    def consume(self) -> Sample[Quantity]:

        sample = self._latest_sample
        if sample is None:
            if self._no_more_data:
                raise ReceiverStoppedError(self)
            raise(RuntimeError("Weird: consume called before ready"))
        self._latest_sample = None
        return sample


def list_microgrid_components_data_receiver(
    client: ReportingApiClient,
    *,
    microgrid_components: list[tuple[int, list[int]]],
    metrics: Metric | list[Metric],
    start_dt: datetime,
    end_dt: datetime,
    resolution: int | None,
    include_states: bool = False,
    include_bounds: bool = False,
) -> Receiver[Sample[Quantity]]:

    stream = client._list_microgrid_components_data_batch(
        microgrid_components=microgrid_components,
        metrics=metrics,
        start_dt=start_dt,
        end_dt=end_dt,
        resolution=resolution,
        include_states=include_states,
        include_bounds=include_bounds,
    )
    return _BatchReceiver(stream)



