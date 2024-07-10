#!/bin/bash

REPO_ROOT=$(git rev-parse --show-toplevel)

python3 $REPO_ROOT/python/tools.py -t FileHeaderUpdate --scope all
