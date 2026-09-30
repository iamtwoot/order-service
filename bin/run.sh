#!/bin/bash
set -e

alembic upgrade head

python -m bin.api &
python -m bin.outbox &
python -m bin.consumer &

trap 'kill -TERM $(jobs -p) 2>/dev/null' TERM INT

status=0
wait -n || status=$?
kill -TERM $(jobs -p) 2>/dev/null || true
wait || true
exit "$status"