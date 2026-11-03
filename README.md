# Medical Chatbot

A document-grounded medical-information prototype using Flask, LangChain, FastEmbed,
Qdrant, and Groq. It is an educational tool, not a medical device: it is not clinically
validated and must not be used to diagnose, prescribe, or delay professional care.
Do not submit personally identifiable or sensitive health information.

## Architecture

- **Frontend:** static HTML, CSS, and JavaScript hosted on Firebase Hosting, or served
  locally by Flask.
- **API:** Flask application served by Gunicorn on Render.
- **Retrieval:** PDF text is split into chunks, embedded with
  `sentence-transformers/all-MiniLM-L6-v2`, and stored in Qdrant.
- **Generation:** LangChain passes retrieved context to the configured Groq model.

The browser sends questions to `POST /get`. `GET /health` checks process liveness;
`GET /ready` reports whether retrieval and generation initialized successfully.
Health checks do not prove answer quality.

## Local setup

1. Use Python 3.11 and create/activate a virtual environment.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Configure `GROQ_API_KEY`. For remote Qdrant, also set `QDRANT_URL` and
   `QDRANT_API_KEY`. Without a Qdrant URL, the application uses local `qdrant_db`
   storage. Keep credentials in an ignored local `.env` file or environment variables;
   never put them in frontend code or source control.
4. Put approved PDF source documents in `data/`, then index them:

   ```bash
   python store_index.py
   ```

5. Start the development server and open `http://127.0.0.1:8080`:

   ```bash
   python app.py
   ```

## Tests

Run the backend regression suite:

```bash
python -m unittest discover -v
```

Tests use mocked services and do not require live model or Qdrant credentials.

## Deployment

The Render Blueprint in `render.yaml` deploys the Flask API. Configure
`GROQ_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY` as Render secrets. Deploy the static
site from `static/` to Firebase Hosting and set `CHATBOT_API_BASE_URL` in
`static/config.js` to the deployed API base URL. The backend `FRONTEND_ORIGINS`
setting must list the exact frontend origins.

After deployment, check `/health` for process status and `/ready` for RAG readiness.
The API returns a not-ready response until a model and compatible Qdrant collection
are available. Free-tier sleep, quotas, provider outages, and latency may affect
availability. The GitHub Actions workflow runs tests; it does not deploy to AWS.

## Limitations

- The answer quality depends on the coverage and quality of indexed documents.
- Responses do not currently include source citations or page references.
- There is no user authentication, rate limiting, conversation history, or clinical
  validation.
- Do not use the project with patient records or for medical decisions.
