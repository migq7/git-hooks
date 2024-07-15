#!/bin/bash

SCRIPT_DIR=$(dirname $(realpath "$0"))

python3 $SCRIPT_DIR/../python/tools.py -t FileHeaderUpdate --scope all
