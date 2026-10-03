#!/bin/bash
# usage: srv.sh start|stop <port> [server args...]
cd "$(dirname "$0")/.."
PY=${PY:-venv/bin/python}
cmd=$1; port=$2; shift 2
pf=logs/srv_$port.pid
case $cmd in
 stop) [ -f $pf ] && kill $(cat $pf) 2>/dev/null; rm -f $pf;;
 start) [ -f $pf ] && kill $(cat $pf) 2>/dev/null; sleep 0.5
   nohup $PY scripts/edge_server.py --port $port "$@" > logs/edge_server_$port.log 2>&1 &
   echo $! > $pf; sleep 3;;
esac
