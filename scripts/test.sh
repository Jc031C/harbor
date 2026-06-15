#!/usr/bin/env bash
set -e

echo "Running Harbor tests..."
python -m unittest discover -s tests
