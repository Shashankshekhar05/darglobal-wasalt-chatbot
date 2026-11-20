# DarGlobal + Wasalt AI Assistant

AI chatbot that answers only from scraped data of DarGlobal and Wasalt. No guessing. No fake prices. If data is not available, it says "Not available".

**Live Demo:** https://darglobal-wasalt-chatbot.onrender.com

## What it does

- Search DarGlobal projects (47 projects)
- Search Wasalt listings (146 listings - 76 for sale + 70 for rent)
- Answers in English only
- Every answer shows original Source URL
- Price not available? Shows "Price: Not available" - never guesses price / ROI / Golden Visa

## Tech Stack

- Python + FastAPI
- TF-IDF + Semantic Retriever
- Groq LLM (openai/gpt-oss-20b) - Free API
- Docker

## How to run locally

```
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000

## Data

- data/darglobal_projects.json
- data/wasalt_listings.json

## Example Questions

- Show me DarGlobal projects in Dubai
- What is DG1?
- Show me villas for rent in Riyadh on Wasalt
- I want a big house in Riyadh for my family
