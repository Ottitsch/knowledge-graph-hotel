#!/usr/bin/env bash
set -euo pipefail

export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"
export NEO4J_REQUIRED="${NEO4J_REQUIRED:-false}"
export PORT="${PORT:-8000}"
export NEO4J_INIT_ON_START="${NEO4J_INIT_ON_START:-true}"
export FORCE_NEO4J_REBUILD="${FORCE_NEO4J_REBUILD:-false}"

NEO4J_HOME="${NEO4J_HOME:-/var/lib/neo4j}"
CYPHER_SHELL="${NEO4J_HOME}/bin/cypher-shell"

set_config() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "${NEO4J_HOME}/conf/neo4j.conf"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "${NEO4J_HOME}/conf/neo4j.conf"
  else
    echo "${key}=${value}" >> "${NEO4J_HOME}/conf/neo4j.conf"
  fi
}

set_config "server.default_listen_address" "0.0.0.0"
set_config "server.bolt.listen_address" "0.0.0.0:7687"
set_config "server.http.listen_address" "0.0.0.0:7474"

if [ ! -f "${NEO4J_HOME}/data/dbms/auth.ini" ]; then
  neo4j-admin dbms set-initial-password "${NEO4J_PASSWORD}" || true
fi

neo4j start

echo "Waiting for Neo4j Bolt at ${NEO4J_URI} ..."
for attempt in $(seq 1 90); do
  if "${CYPHER_SHELL}" -a "${NEO4J_URI}" -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" "RETURN 1" >/dev/null 2>&1; then
    break
  fi
  if [ "${attempt}" = "90" ]; then
    echo "Neo4j did not become ready in time." >&2
    neo4j status || true
    exit 1
  fi
  sleep 2
done

if [ "${NEO4J_INIT_ON_START}" = "true" ]; then
  node_count="$("${CYPHER_SHELL}" -a "${NEO4J_URI}" -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" --format plain "MATCH (n) RETURN count(n) AS count" | tail -n 1 | tr -d '\r[:space:]')"
  if [ "${FORCE_NEO4J_REBUILD}" = "true" ] || [ "${node_count:-0}" = "0" ]; then
    echo "Initializing Neo4j graph from project data ..."
    python /app/src/construct/build_graph.py
  else
    echo "Neo4j already contains ${node_count} nodes; skipping graph initialization."
  fi
fi

exec gunicorn webapp.app:app \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads "${WEB_THREADS:-4}" \
  --timeout "${WEB_TIMEOUT:-120}"
