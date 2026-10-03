#!/bin/bash
# Reproduces every log in logs/. Needs: python>=3.11, node>=20 (for the TS comparison), curl.
set -e
cd "$(dirname "$0")"
export MCP_USE_ANONYMIZED_TELEMETRY=false
python3 -m venv venv && ./venv/bin/pip install -q -r requirements.txt
mkdir -p logs
scripts/srv.sh start 8765                       # paginated server (page size 2), stateful streamable HTTP
./venv/bin/python scripts/pagination_probe.py            | tee logs/pagination_probe.out
./venv/bin/python scripts/pagination_agent_path.py       | tee logs/pagination_agent_path.out
./venv/bin/python scripts/session_expiry_probe.py        | tee logs/session_expiry_probe.out
scripts/srv.sh start 8766 --stateless --json
./venv/bin/python scripts/pagination_probe.py http://127.0.0.1:8766/mcp/ | tee logs/pagination_probe_stateless_json.out
scripts/srv.sh stop 8766
./venv/bin/python scripts/schema_probe.py                | tee logs/schema_probe.out
(cd ts-probe && npm install --silent && node probe.mjs http://127.0.0.1:8765/mcp/ | tee ../logs/pagination_probe_ts.out)
scripts/srv.sh stop 8765
