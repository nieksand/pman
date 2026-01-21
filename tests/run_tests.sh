#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"
PYTHONPATH="$SCRIPT_DIR/.." python3 -m unittest discover -v -s "$SCRIPT_DIR" -p "*.py"
