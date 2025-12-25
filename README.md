# 🔬 Deep Research Agent
> *A production-grade, autonomous AI research assistant that doesn't just search—it understands.*

---

## 📖 Overview

The **Deep Research Agent** is a cutting-edge AI system designed to conduct exhaustive, fact-based research on any complex topic. Unlike standard chatbots that hallucinate or skim the surface, this agent employs a multi-stage **Planner-Searcher-Summarizer-Writer** pipeline to ensure every report is comprehensive, accurate, and cited.

Built for stability and precision, it leverages **Serper.dev** for real-time Google Search data and a stringent anti-hallucination architecture to deliver professional-grade research reports in minutes.

## ✨ Key Features

- **🧠 Autonomous Planning**: The agent analyzes your request and generates a targeted 10-15 step search plan to cover every angle of the topic.
- **🔍 Verified Ground Truth**: Replaces unstable scrapers with the official **Google Search API (via Serper)** for reliable, noise-free results.
- **🛡️ Anti-Hallucination Pipeline**: Adopts a strict `Plan -> Search -> Synthesize` workflow. The agent is grounded in retrieved facts, preventing the "creative" invention of information.
- **⚡ Smart Caching**: Implements MD5 hashed caching to store search results locally. Recurring queries are instant and cost zero API credits.
- **📝 Deep-Dive Reporting**: Generates 9,000+ word exhaustive reports (configurable) with clear sections, executive summaries, and citations.
- **💻 Modern UI**: Includes a clean, dark-mode **Gradio** web interface for easy interaction.

## ⚙️ How It Works

1.  **Planner Agent**: Deconstructs your query into key dimensions (background, mechanisms, applications, risks) and creates a specific search checklist.
2.  **Search Loop**: Executes executed searches in parallel or sequence, respecting rate limits to ensure stability.
3.  **Summarizer Agent**: Reads through raw search snippets and pages, distilling them into fact-dense summaries while preserving context.
4.  **Writer Agent**: Synthesizes the aggregated knowledge into a structured, Markdown-formatted report, complete with a confidence score and key findings.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **OpenAI API Key** (for the reasoning engine)
- **Serper.dev API Key** (for Google Search capabilities - includes 2,500 free queries)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/Deep-Research-Agent.git
    cd "Deep Research Agent"
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory and add your keys:
    ```env
    OPENAI_API_KEY=sk-your-openai-key-here
    SERPER_API_KEY=your-serper-key-here
    ```

### Running the Agent

Launch the web interface with a single command:

```bash
python app.py
```

The application will start locally (usually at `http://127.0.0.1:7860`). Open the link in your browser, enter your research topic, and watch the agent go to work!

## 📂 Project Structure

- `app.py`: The entry point. Handles the Gradio UI and user interaction.
- `deep_research_agent.py`: The core logic containing the Agent definitions, the search pipeline, and the synthesis engine.
- `research_cache.json`: Automatically generated file that stores search results to speed up future queries.
- `.env`: (Created by you) Stores your API credentials securely.

## 🤝 Contributing

Contributions are welcome! Whether it's adding new search providers, improving the report format, or optimizing the planning algorithm, feel free to fork the repo and submit a pull request.

## 📄 License

This project is open-source and available for personal and educational use.
