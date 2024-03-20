# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Examples usage of reporting API."""

import argparse
import asyncio
from datetime import datetime
from pprint import pprint
from typing import AsyncGenerator

import pandas as pd
from frequenz.client.common.metric import Metric

from frequenz.client.reporting import ReportingClient

# Experimental import
from frequenz.client.reporting._client import MetricSample


# pylint: disable=too-many-locals
async def main(microgrid_id: int, component_id: int) -> None:
    """Test the ReportingClient.

    Args:
        microgrid_id: int
        component_id: int
    """
    service_address = "localhost:50051"
    client = ReportingClient(service_address)

    microgrid_components = [(microgrid_id, [component_id])]
    metrics = [
        Metric.DC_POWER,
        Metric.DC_CURRENT,
    ]

    start_dt = datetime.fromisoformat("2023-11-21T12:00:00.00+00:00")
    end_dt = datetime.fromisoformat("2023-11-21T12:01:00.00+00:00")

    page_size = 10

    print("########################################################")
    print("Iterate over single metric generator")

    async for sample in client.iterate_single_metric(
        microgrid_id=microgrid_id,
        component_id=component_id,
        metric=metrics[0],
        start_dt=start_dt,
        end_dt=end_dt,
        page_size=page_size,
    ):
        print("Received:", sample)

    ###########################################################################
    #
    # The following code is experimental and demonstrates potential future
    # usage of the ReportingClient.
    #
    ###########################################################################

    async def components_data_iter() -> AsyncGenerator[MetricSample, None]:
        """Iterate over components data.

        Yields:
            Single metric sample
        """
        # pylint: disable=protected-access
        async for page in client._iterate_components_data_pages(
            microgrid_components=microgrid_components,
            metrics=metrics,
            start_dt=start_dt,
            end_dt=end_dt,
            page_size=page_size,
        ):
            for entry in page.iterate_metric_samples():
                yield entry

    async def components_data_dict(
        components_data_iter: AsyncGenerator[MetricSample, None]
    ) -> dict[int, dict[int, dict[datetime, dict[Metric, float]]]]:
        """Convert components data iterator into a single dict.

            The nesting structure is:
            {
                microgrid_id: {
                    component_id: {
                        timestamp: {
                            metric: value
                        }
                    }
                }
            }

        Args:
            components_data_iter: async generator

        Returns:
            Single dict with with all components data
        """
        ret: dict[int, dict[int, dict[datetime, dict[Metric, float]]]] = {}

        async for ts, mid, cid, met, value in components_data_iter:
            if mid not in ret:
                ret[mid] = {}
            if cid not in ret[mid]:
                ret[mid][cid] = {}
            if ts not in ret[mid][cid]:
                ret[mid][cid][ts] = {}

            ret[mid][cid][ts][met] = value

        return ret

    print("########################################################")
    print("Iterate over generator")
    async for msample in components_data_iter():
        print("Received:", msample)

    print("########################################################")
    print("Dumping all data as a single dict")
    dct = await components_data_dict(components_data_iter())
    pprint(dct)

    print("########################################################")
    print("Turn data into a pandas DataFrame")
    data = [cd async for cd in components_data_iter()]
    df = pd.DataFrame(data).set_index("timestamp")
    pprint(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("microgrid_id", type=int, help="Microgrid ID")
    parser.add_argument("component_id", type=int, help="Component ID")

    args = parser.parse_args()
    asyncio.run(main(args.microgrid_id, args.component_id))
