# Deep Research Agent

An AI-powered research assistant with a modern Gradio interface. This tool automates deep research on any given topic using OpenAI models and DuckDuckGo search, providing detailed reports, key findings, and research metrics.

## Features

- **Interactive Web UI**: Clean, responsive interface built with Gradio.
- **Deep Research**: Automated planning and execution of research on complex topics.
- **Comprehensive Reports**:
  - **Research Strategy**: Visualizes the search queries and reasoning.
  - **Key Findings**: Bulleted list of critical information.
  - **Detailed Analysis**: extensive breakdown of the topic.
  - **Confidence Score**: AI-generated confidence rating of the findings.
- **Smart Caching**: Local JSON caching to reduce API costs and speed up repeated searches.
- **Metrics Dashboard**: Tracks API calls, estimated costs, duration, and number of searches.

## Prerequisites

- Python 3.8+
- OpenAI API Key

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd "Deep Research Agent"
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a `.env` file in the root directory.
2.  Add your API keys (e.g., OpenAI API Key):
    ```env
    OPENAI_API_KEY=your_api_key_here
    ```

> **Note:** The `.env` file is git-ignored to keep your secrets safe.

## Usage

Run the application:

```bash
python app.py
```

The application will launch locally at `http://localhost:7860`.

## Project Structure

- **app.py**: The main entry point containing the Gradio UI and frontend logic.
- **deep_research_agent.py**: Contains the core logic for the research agent, including planning, searching, and report synthesis.
- **requirements.txt**: Python package dependencies.
- **.gitignore**: Specifies files to be ignored by Git (including `.env`).

## Dependencies

- [Gradio](https://www.gradio.app/): For the web interface.
- [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/): For fetching search results.
- [OpenAI Agents](https://pypi.org/project/openai-agents/): For AI agent capabilities.
- [Pydantic](https://docs.pydantic.dev/): For data validation.
- [Python-Dotenv](https://pypi.org/project/python-dotenv/): For environment variable management.
