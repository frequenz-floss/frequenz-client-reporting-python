# Frequenz Reporting API Client

[![Build Status](https://github.com/frequenz-floss/frequenz-client-reporting-python/actions/workflows/ci.yaml/badge.svg)](https://github.com/frequenz-floss/frequenz-client-reporting-python/actions/workflows/ci.yaml)
[![PyPI Package](https://img.shields.io/pypi/v/frequenz-client-reporting)](https://pypi.org/project/frequenz-client-reporting/)
[![Docs](https://img.shields.io/badge/docs-latest-informational)](https://frequenz-floss.github.io/frequenz-client-reporting-python/)

## Introduction

A Python client for interacting with the Frequenz Reporting API to efficiently retrieve metric and state data from microgrids.

> **Who should use this?**
> This client is for developers building applications on top of Frequenz's platform who need structured access to historical component or sensor data via Python or CLI.


## Supported Platforms

The following platforms are officially supported (tested):

- **Python:** 3.11
- **Operating System:** Ubuntu Linux 20.04
- **Architectures:** amd64, arm64

## Contributing

If you want to know how to build this project and contribute to it, please
check out the [Contributing Guide](CONTRIBUTING.md).


## Usage

Please also refer to [examples](https://github.com/frequenz-floss/frequenz-client-reporting-python/tree/HEAD/examples) for more detailed usage.

### Installation

```bash
# Choose the version you want to install
VERSION=0.18.0
pip install frequenz-client-reporting==$VERSION
```


### Initialize the client

To use the Reporting API client, you need to initialize it with the server URL and authentication credentials.
The server URL should point to your Frequenz Reporting API instance, and you will need an authentication key and a signing secret.

> **Security Note**
> Always keep your authentication key and signing secret secure. Do not hard-code them in your source code or share them publicly.

```python
from datetime import datetime, timedelta
import os

from frequenz.client.common.metric import Metric
from frequenz.client.reporting import ReportingApiClient

# Change server address
SERVER_URL = "grpc://replace-this-with-your-server-url:port"
AUTH_KEY = os.environ['REPORTING_API_AUTH_KEY'].strip()
# It is recommended to use a proper secret store to get the secret
# For local development, make sure not to leave it in the shell history
SIGN_SECRET= os.environ['REPORTING_API_SIGN_SECRET'].strip()
client = ReportingApiClient(server_url=SERVER_URL, auth_key=AUTH_KEY, sign_secret=SIGN_SECRET)
```

### Query metrics for a single microgrid and component

This method supports:
- Selecting specific `microgrid_id` and `component_id`
- Choosing one or more `metrics` to retrieve
- Defining a time range with `start_time` and `end_time`
- Optional downsampling using `resampling_period` (e.g., `timedelta(minutes=15)`)

```python
# Asynchronously collect metric data samples into a list
data = [
    sample async for sample in
    client.receive_single_component_data(
        microgrid_id=1,  # ID of the microgrid to query
        component_id=100,  # ID of the specific component to query
        metrics=[  # List of metrics to retrieve
            Metric.AC_ACTIVE_POWER,      # AC active power
            Metric.AC_REACTIVE_POWER,      # AC reactive power
        ],
        start_time=datetime.fromisoformat("2024-05-01T00:00:00"),  # Start of query range (UTC)
        end_time=datetime.fromisoformat("2024-05-02T00:00:00"),    # End of query range (UTC)
        resampling_period=timedelta(seconds=5),  # Optional: downsample data to 5-second intervals
    )
]
```


### Query metrics for a single microgrid and sensor

To query sensor data for a specific microgrid, you can use the following method.

```python
data = [
    sample async for sample in
    client.receive_single_sensor_data(
        microgrid_id=1,
        sensor_id=100,
        metrics=[Metric.SENSOR_IRRADIANCE],
        start_time=datetime.fromisoformat("2024-05-01T00:00:00"),
        end_time=datetime.fromisoformat("2024-05-02T00:00:00"),
        resampling_period=timedelta(seconds=1),
    )
]
```


### Query metrics for multiple microgrids and components

It is possible to query data for multiple microgrids and their components in a single request.

```python
# Set the microgrid ID and the component IDs that belong to the microgrid
# Multiple microgrids and components can be queried at once
microgrid_id1 = 1
component_ids1 = [100, 101, 102]
microgrid_id2 = 2
component_ids2 = [200, 201, 202]
microgrid_components = [
    (microgrid_id1, component_ids1),
    (microgrid_id2, component_ids2),
]

data = [
    sample async for sample in
    client.receive_microgrid_components_data(
        microgrid_components=microgrid_components,
        metrics=[Metric.AC_ACTIVE_POWER, Metric.AC_REACTIVE_POWER],
        start_time=datetime.fromisoformat("2024-05-01T00:00:00"),
        end_time=datetime.fromisoformat("2024-05-02T00:00:00"),
        resampling_period=timedelta(seconds=1),
        include_states=False, # Set to True to include state data
        include_bounds=False, # Set to True to include metric bounds data
    )
]
```

### Query metrics for multiple microgrids and sensors

Similar to the previous example, you can query multiple microgrids and their sensors in a single request.

```python
# Set the microgrid ID and the sensor IDs that belong to the microgrid
# Multiple microgrids and sensors can be queried at once
microgrid_id1 = 1
sensor_ids1 = [100, 101, 102]
microgrid_id2 = 2
sensor_ids2 = [200, 201, 202]
microgrid_sensors = [
    (microgrid_id1, sensor_ids1),
    (microgrid_id2, sensor_ids2),
]

data = [
    sample async for sample in
    client.receive_microgrid_sensors_data(
        microgrid_sensors=microgrid_sensors,
        metrics=[Metric.SENSOR_IRRADIANCE],
        start_time=datetime.fromisoformat("2024-05-01T00:00:00"),
        end_time=datetime.fromisoformat("2024-05-02T00:00:00"),
        resampling_period=timedelta(seconds=1),
        include_states=False, # Set to True to include state data
    )
]
```

### Optionally convert the data to a pandas DataFrame

For easier data manipulation and analysis, you can convert the collected data into a pandas DataFrame.

```python
import pandas as pd
df = pd.DataFrame(data)
print(df)
```

## Command line client tool

The package contains a command-line tool that can be used to request
microgrid component data from the reporting API.

```bash
reporting-cli \
    --url localhost:4711 \
    --auth_key=$AUTH_KEY
    --sign_secret=$SIGN_SECRET
    --mid 42 \
    --cid 23 \
    --metrics AC_ACTIVE_POWER AC_REACTIVE_POWER \
    --start 2024-05-01T00:00:00 \
    --end 2024-05-02T00:00:00 \
    --format csv \
    --states \
    --bounds
```
In addition to the default CSV format, individual samples can also be output using the `--format iter` option.
