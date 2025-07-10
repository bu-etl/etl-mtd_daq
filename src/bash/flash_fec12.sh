#!/bin/bash

cd /home/cmx/mtd-emp-toolbox/mtd-daq
source ../scripts/env.sh
source ../scripts/env.sh
python3 init_Serenity.py -fpga x0 -dir /home/cmx/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL -bit 'lpGBTv2_3_SO1.bit' -xml 'hls_connections.xml'

