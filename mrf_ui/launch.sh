#!/bin/bash
# savonius_mrf kontrol paneli baslatici
DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PORT=8877

if ! curl -s "http://127.0.0.1:${PORT}/" -o /dev/null; then
    cd "$DIR" || exit 1
    nohup python3 server.py > server.log 2>&1 &
    sleep 1
fi

xdg-open "http://127.0.0.1:${PORT}/" 2>/dev/null &
