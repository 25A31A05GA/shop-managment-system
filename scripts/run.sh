#!/usr/bin/env bash
# ./scripts/run.sh            -> morning brief
# ./scripts/run.sh serve      -> API on :8080
cd "$(dirname "$0")/.." && python3 -m dukan_drishti "${@:-brief}"
