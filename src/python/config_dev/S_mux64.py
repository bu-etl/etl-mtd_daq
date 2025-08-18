'''
Info: Testing MUX64 communication
'''

import time
import sys
from ..controllers.lpgbt_controller import *
from ..controllers.mux64_controller import mux64_chip
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lpgbt")

lpgbt = lpgbt_chip(
    "Master LPGBT",
    connection="~/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml",
    link=4,
    lpgbt_address="0x73"
    )
lpgbt.lpgbt_cont_.set_multiwrite(False)
lpgbt.init_lpgbt()
mux64 = mux64_chip(lpgbt, board="Readout Board")

mux64.write_config()
mux64.calibrate_adc()
#adc_regs = [
#"DACCONFIGH",
#"CURDACVALUE",
#"CURDACCHN",
#"VREFCNTR",
#"VREFTUNE"
#]
#for r in adc_regs:
#    lr = lpgbt.read_reg(lpgbt.Reg[r])
#    print(f"reg={r} | {lr}, {hex(lr)}")

#mux64.read_config()
#for r in adc_regs:
#    lr = lpgbt.read_reg(lpgbt.Reg[r])
#    print(f"reg={r} | {lr}, {hex(lr)}")

mux64.read_all_ch()
