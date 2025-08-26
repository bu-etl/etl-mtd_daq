#!/bin/bash

SRC_DIR="/home/cmx/etl/toolbox/mtd-emp-toolbox/mtd-daq-etl/src/mtddaqsw/apps"
DEST_DIR="/home/cmx/etl/MTD_DAQ_etl-Tests/src/python"

# Create destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Copy files starting with 'etl'
cp "$SRC_DIR"/etl* "$DEST_DIR"