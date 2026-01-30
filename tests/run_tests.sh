#!/bin/bash
PYTHONPATH=$(dirname $0)/.. python3 -m unittest -v $(dirname $0)/*.py
