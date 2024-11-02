# Restaurant assistant demo using LLM agents and Streamlit

This demo application showcases how to use Streamlit and Large Language Model (LLM) agents to get restaurant recommendations.

## Features

- **Interactive UI**: Built with Streamlit for a seamless user experience.
- **LLM Integration**: Utilizes advanced language models to provide personalized restaurant suggestions.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/llmagents.git
    cd llmagents/autogenstreamlit
    ```

2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```

2. Open your web browser and go to `http://localhost:8501` to interact with the app.

## How It Works

- **User Input**: Enter your preferences and location.
- **LLM Processing**: The input is processed by an LLM agent to generate recommendations.
- **Output**: The app displays a list of recommended restaurants.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.


## Development steps:

Streamlit requires python version 3.12. With version 3.13 it fails with error https://stackoverflow.com/questions/74254073/installation-error-streamlit-building-wheel-for-pyarrow-pyproject-toml-er

1. Create Python environment

```bash
conda create -n autogen+streamlit python=3.12
```

1. Activate environment
   
```bash
conda activate autogen+streamlit
```

1. Install Streamlit package
   
```bash
pip install streamlit -c .\autogenstreamlit\constrains.txt
```

Notes:
To resolve error:
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
autogen 0.3.1 requires flaml, which is not installed.
autogen 0.3.1 requires openai>=1.3, which is not installed.
autogen 0.3.1 requires tiktoken, which is not installed.
folium 0.17.0 requires xyzservices, which is not installed.

use a constrains.txt file with:

```text
flaml==2.2.0
```

1. Open vscode from Anaconda PowerShell console

code .

## References

- [Streamlit - Build a basic LLM chat app](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
