# Starting from scratch

## Introduction

This tutorial is an opinionated guide intended for people with no experience working with Python and [Jupyter Notebooks](https://jupyter.org/), to help them get started quickly from scratch.

To get started, create a directory for your project and follow the steps below to set up your development environment and run the client.

## Install VS Code

Download and install **Visual Studio Code** from the [official website](https://code.visualstudio.com/).

Once installed, add the following extensions:

- [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)

These enable Python development and interactive notebooks within VS Code.

## Set Up a Virtual Environment

It is recommended to use a **virtual environment** for isolating dependencies.
When using a virtual environment, you create something like a sandbox or containerized workspace that isolates dependencies and packages so they don’t conflict with the system or other projects. After creating the virtual environment, you can install all packages you need for the current project. To set up an initial virtual environment for using the Reporting API, go through the following steps:

### Linux / macOS

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

### Windows (PowerShell)

> [!WARNING]
> Windows is not officially supported **yet**, but in general things should just work. If you find any issues using the client in Windows, please report them.

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

# Deactivate the environment (only when you are finished working with this project)
#deactivate
```

## API Keys

To access the API, a key has to be created via Frequenz Web UI and stored locally on your computer. For that go through the following steps:

### Create a `.env` file

When creating the API key, you will get two keys. One is the API key itself and the other one is the API secret. Go to your projects directory and create a text file named `.env` where you can store the API key and the API secret.
Prepare the text file as follows:

```bash
REPORTING_API_AUTH_KEY=
REPORTING_API_SIGN_SECRET=
```

### Create API Key via Frequenz Web UI

Log into your Frequenz Web UI account and click on your email-address on the bottom left. Then continue with `API keys` and `Create API key`. The created API key will be shown in the UI. This is the only time, the API key will be shown to you. If you lose it, you should remove the lost key from the UI and create a new one.
Copy the API key and the API secret and add it to the `.env` file.

```bash
REPORTING_API_AUTH_KEY=[your-api-key]
REPORTING_API_SIGN_SECRET=[your-api-secret]
```

### Testing the Client

Please also refer to source of the [CLI tool](https://github.com/frequenz-floss/frequenz-client-reporting-python/blob/v0.x.x/src/frequenz/client/reporting/cli/__main__.py)
for a practical example of how to use the client.

## Initial Client and Notebook Setup

### Create a Notebook

Open your project's directory with VS Code. You should see your `.venv` and `.env` files in the directory when using VS Code.
Create a new `.ipynb` file (Jupyter notebook file) in the directory. When selecting the empty ipynb file, you will find `Select Kernel` on the top right of the file. Click on it and select `Jupyter Kernel > Python (myenv)`. Now the notebook will use your virtual environment as an interpreter.

### Initialize the Client

To use the Reporting API client, you need to initialize it with the server URL and authentication credentials.
The server URL should point to your Frequenz Reporting API instance, and you will need an authentication key and a signing secret, as described above.

> **SERVER URL:**
> Please ask your service administrator for the SERVER URL

> **Security Note:**
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

## Next steps

You can now try out the code examples, like the [examples in the README](../index.md#query-metrics-for-a-single-microgrid-and-component).
