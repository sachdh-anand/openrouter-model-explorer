# OpenRouter Model Explorer

![OpenRouter Model Explorer](https://img.shields.io/badge/OpenRouter-Model%20Explorer-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0%2B-red)

A powerful, interactive dashboard to discover, compare, and select the best free and preview AI models available on OpenRouter. Focused on models with coding, reasoning, and tool-calling capabilities.

## 🌟 Features

- **Interactive Filtering**: Filter models by effectiveness score, specific capabilities, and text search
- **Provider Information**: See which company created each model (Anthropic, Google, Meta, etc.)
- **Effectiveness Scoring**: Models ranked by a calculated score (0-10) based on:
  - Context length
  - Parameter size
  - Special capabilities
  - Function/tool support
- **Capability Visualization**: Clear indicators for coding, reasoning, and tool-calling support
- **One-Click Exporting**: Select models and export them as environment variables for your projects

## 📊 Screenshots

![OpenRouter Model Explorer Interface](app_snapshot.png)

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- An OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/openrouter_models.git
   cd openrouter_models
   ```

2. Install dependencies using [`uv`](https://github.com/astral-sh/uv):
   ```bash
   uv pip install -r requirements.txt
   ```

### Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Enter your OpenRouter API key when prompted
3. Browse and filter models based on your requirements
4. Select models to add them to your environment configuration
5. Use the "Copy" button to copy the `.env` format to your clipboard

## 📋 How It Works

The tool connects to OpenRouter's API to fetch comprehensive model data, then:

1. Filters for free and preview models
2. Calculates an effectiveness score (0-10) based on multiple factors
3. Analyzes model descriptions and architecture to identify capabilities
4. Extracts provider information from model IDs
5. Presents results in an interactive table with filtering options

## 🔍 Features Explained

### Effectiveness Score

The effectiveness score (0-10) considers:

- **Context Length**: +1 for >32k tokens, +0.5 for >16k tokens
- **Tool/Function Support**: +1 for tool/function calling capabilities
- **Preview Models**: +0.5 for preview models
- **Model Size**: +1.5 for ≥70B, +1 for ≥30B, +0.5 for ≥7B
- **Specialties**: +1 for models with both coding and reasoning, +1 for tool calling

### Capabilities

Models are analyzed for specific capabilities:

- **🖥️ Code**: Specialized in coding tasks and programming
- **🤔 Reason**: Strong reasoning and logical thinking abilities
- **🔧 Tools**: Support for tool use and function calling

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

This project is MIT licensed. See LICENSE file for details.

## 🙏 Acknowledgements

- [OpenRouter](https://openrouter.ai/) for providing API access to multiple LLMs
- [Streamlit](https://streamlit.io/) for the interactive web framework
- Contributors and users who provide feedback
