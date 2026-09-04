# PrismText

PrismText is a unified visual canvas that turns text into Mermaid diagrams and reconstructs infographic images into structured Markdown summaries using Google Gemini.

## Features

- Text-to-diagram generation with a dark neon Mermaid aesthetic
- Infographic-to-text extraction using Gemini vision
- Single-page Streamlit workspace with side-by-side text and visual canvases
- Gemini API key support through Streamlit secrets or the sidebar

## Requirements

- Python 3.9 or later
- A Google Gemini API key

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set `GEMINI_API_KEY` in Streamlit secrets, or enter it in the application sidebar when it starts.

## Planned structure

```text
.streamlit/config.toml
app.py
requirements.txt
README.md
```
