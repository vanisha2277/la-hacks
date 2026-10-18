# Railway build for the API. Build context is the repo root (see /railway.json).
FROM python:3.12-slim
COPY app/api/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt
# kb.json points at the build machine's SVG paths; the API falls back to CORPUS_DIR/drawings/<name>
COPY unit200_update/unit200_corpus/drawings /srv/unit200_update/unit200_corpus/drawings
COPY app/config.py /srv/app/config.py
COPY app/core /srv/app/core
COPY app/agents /srv/app/agents
COPY app/api /srv/app/api
COPY app/agentverse /srv/app/agentverse
COPY app/out/kb.json /srv/app/out/kb.json
WORKDIR /srv/app
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
