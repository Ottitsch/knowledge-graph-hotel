# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend

WORKDIR /app/webapp/frontend
COPY webapp/frontend/package*.json ./
RUN npm ci

COPY webapp/frontend/ ./
RUN npm run build


FROM neo4j:5.26-community AS runtime

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    NEO4J_AUTH=neo4j/password \
    NEO4J_URI=bolt://localhost:7687 \
    NEO4J_USER=neo4j \
    NEO4J_PASSWORD=password \
    NEO4J_REQUIRED=false \
    NEO4J_server_default__listen__address=0.0.0.0 \
    NEO4J_server_bolt_listen__address=0.0.0.0:7687 \
    NEO4J_server_http_listen__address=0.0.0.0:7474

WORKDIR /app

COPY requirements-docker.txt ./
RUN python3 -m venv /opt/app-venv \
    && /opt/app-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/app-venv/bin/pip install --no-cache-dir -r requirements-docker.txt

ENV PATH="/opt/app-venv/bin:${PATH}"

COPY src ./src
COPY webapp ./webapp
COPY data ./data
COPY graph ./graph
COPY models ./models
COPY ontology ./ontology
COPY reports ./reports
COPY --from=frontend /app/webapp/frontend/dist ./webapp/frontend/dist
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && chown -R neo4j:neo4j /app /opt/app-venv /entrypoint.sh

USER neo4j

EXPOSE 8000 7474 7687

ENTRYPOINT ["/entrypoint.sh"]
