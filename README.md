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

## Getting Started

To get started, create a directory for your project and follow the steps below to set up your development environment and run the client.

### 1. Install VS Code

Download and install **Visual Studio Code** from the [official website](https://code.visualstudio.com/).

Once installed, add the following extensions:

- [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)  
- [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)  

These enable Python development and interactive notebooks within VS Code.

### 2. Set Up a Virtual Environment

It is recommended to use a **virtual environment** for isolating dependencies.
When using a virtual environment, you create something like a sandbox or containerized workspace that isolates dependencies and packages so they don’t conflict with the system or other projects. After creating the virtual environment, you can install all packages you need for the current project. To set up an initial virtual environment for using the Reporting API, go through the following steps:

#### Linux / macOS

```bash
### Go to your projects directory, open a terminal and run the following commands

# Create a virtual environment
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate # when using bash
source .venv/bin/activate.fish # when using fish

# Install the version of the reporting client you want to use
pip install frequenz-client-reporting==0.18.0

# Install python-dotenv
# --> Used to load environment variables from a `.env` file into the projects environment
pip install python-dotenv

# Install ipkernel
# --> Python execution backend for Jupyter
pip install ipkernel

# Register the virtual environment as a kernel
python -m ipykernel install --user --name=myenv --display-name "Python (myenv)"

# Install pandas
pip install pandas

# Deactivate the environment
deactivate
```

#### Windows (PowerShell)

```powershell
### Go to your projects directory, open PowerShell and run the following commands

# Create a virtual environment
python -m venv .venv

# Activate the environment
.venv\Scripts\Activate.ps1

# Install the version of the reporting client you want to use
pip install frequenz-client-reporting==0.18.0

# Install python-dotenv
# --> Used to load environment variables from a `.env` file into the project's environment
pip install python-dotenv

# Install ipykernel
# --> Python execution backend for Jupyter
pip install ipykernel

# Register the virtual environment as a kernel
python -m ipykernel install --user --name=myenv --display-name "Python (myenv)"

# Install pandas
pip install pandas

# Deactivate the environment
deactivate
```

## Create API Keys via Kuiper

To access the API, a key has to be created via Kuiper and stored locally on your computer. For that go through the following steps:

### 1 create .env file

When creating the API key, you will get two keys. One is the API key itself and the other one is the API secret. Go to your projects directory and create a textfile named ".env" in your project folder where you can store the API key and the API secret.
Prepare the textfile as follows:

```bash
# .env
REPORTING_API_AUTH_KEY=
REPORTING_API_SIGN_SECRET=
```

### 2 Create API key via Kuiper

Log into your Kuiper account and click on your email-address on the bottom left. Then continue with "API keys" and "Create API key". The created API key will be shown in the UI. This is the only time, the API key will be shown to you. whenever you loose it, you have to create a new one.
Copy the API key and the API secret and add it to the .env file.

```bash
# .env
REPORTING_API_AUTH_KEY=EtQurK8LXA8vmEd4M6DqxeNp
REPORTING_API_SIGN_SECRET=DCG5x7XrJa2hN3spRTjVyQk9w16xXqR6hEUkYcoCG9yjx7Pp
```

## Usage

Please also refer to source of the [CLI tool](https://github.com/frequenz-floss/frequenz-client-reporting-python/blob/v0.x.x/src/frequenz/client/reporting/cli/__main__.py)
for a practical example of how to use the client.

### Create a notebook

Open your projects directory with VS Code. You should see your .venv and .env files in the directory when using VS Code.
Create a new .ipynb file (Jupyter notebook file) in the directory. When selecting the empty ipynb file, you will find "Select Kernel" on the top right of the file. Click on it and select "Jupyter Kernel" > "Python (myenv). Now the notebook will use your virtual environment as an interpreter.

### Initialize the client

To use the Reporting API client, you need to initialize it with the server URL and authentication credentials.
The server URL should point to your Frequenz Reporting API instance, and you will need an authentication key and a signing secret, as described above.

> **Security Note**
> Always keep your authentication key and signing secret secure. Do not hard-code them in your source code or share them publicly.

```python
# Import basic packages
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import pandas as pd

# Import Metrics and ReportingApiClient
from frequenz.client.common.metric import Metric
from frequenz.client.reporting import ReportingApiClient

# Read the API key from .env and sets it as environment variables in the current python process
load_dotenv()

# Create Reporting API Client
SERVER_URL = "grpc://replace-this-with-your-server-url:port"
AUTH_KEY = os.environ['REPORTING_API_AUTH_KEY'].strip()
SIGN_SECRET= os.environ['REPORTING_API_SIGN_SECRET'].strip()
client = ReportingApiClient(server_url=SERVER_URL, auth_key=AUTH_KEY, sign_secret=SIGN_SECRET)
```

### Query metrics for a single microgrid and component

This method supports:
- Selecting specific `microgrid_id` and `component_id`.
- Choosing one or more `metrics` to retrieve. Available metrics are listed [here](https://frequenz-floss.github.io/frequenz-api-common/v0.8/protobuf-reference/frequenz/api/common/v1alpha8/metrics/metrics/#frequenz-api-common-v1alpha8-metrics-Metric).
- Defining a time range with `start_time` and `end_time`.
- Optional downsampling using `resampling_period` (e.g., `timedelta(minutes=15)`).

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

## Usage of formulas

Formulas can be used to calculate a metric aggregated over multiple components or sensors.
Note that this endpoint must be used with a `resampling_period`.
Details on the formula syntax can be found [here](https://github.com/frequenz-floss/frequenz-microgrid-formula-engine-rs/tree/v0.x.x?tab=readme-ov-file#formula-syntax-overview).

```python
# Example formula to sum the values of two components.
formula = "#1 + #2"
data = [
    sample async for sample in
    client.receive_aggregated_data(
        microgrid_id=microgrid_id,
        metric=Metric.AC_ACTIVE_POWER,
        aggregation_formula=formula,
        start_time=datetime.fromisoformat("2024-05-01T00:00:00"),
        end_time=datetime.fromisoformat("2024-05-02T00:00:00"),
        resampling_period=resampling_period,
    )
]
```

## Optionally convert the data to a pandas DataFrame

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
