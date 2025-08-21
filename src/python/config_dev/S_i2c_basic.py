"""
Authors: Hayden and Naomi
Date: August 18, 2025

def i2c_master_write(
    self,
    master_id,
    slave_address,
    reg_address_width,
    reg_address,
    data,
    timeout=0.1,
    addr_10bit=False,
):
    
    Performs a register-based write using an lpGBT I2C master.
    Register address is placed LSbyte first in the transaction data buffer,
    followed by the register contents (variable length).

    Errata note: 16 byte writes (including address and data) are only possible
    as specified in 7 bit slave addressing mode. When 10 bit addressing mode is
    used, the maximum number of bytes in a transaction is 15.

    Arguments:
        master_id: lpGBT I2C master to use
        slave_address: I2C slave bus address
        reg_address_width: length of register address in bytes
        reg_address: slave register write address
        data: data to write (single byte or list of bytes)
        timeout: I2C write completion timeout
        addr_10bit: enable 10-bit addressing format

@lpgbt_accessor
def i2c_master_read(
    self,
    master_id,
    slave_address,
    read_len,
    reg_address_width,
    reg_address,
    timeout=0.1,
    addr_10bit=False,
):
    Performs a register-based read using an lpGBT I2C master.
    Register address pointer is written to the slave using a write
    transaction. Then, a multi-byte read transction is triggered to read
    slave register contents.

    Errata note: 16 byte reads (including address and data) are only possible
    as specified in 7 bit slave addressing mode. When 10 bit addressing mode is
    used, the maximum number of bytes in a transaction is 15.

    Arguments:
        master_id: lpGBT I2C master to use
        slave_address: I2C slave bus address
        read_len: number of bytes to read from slave
        reg_address_width: length of register address in bytes
        reg_address: slave register read address
        timeout: I2C write completion timeout
        addr_10bit: enable 10-bit addressing format
"""

import time
import sys
from ..controllers.lpgbt_controller import *
import logging
from functools import partial
from ..controllers.mux64_controller import mux64_chip

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

print("sleeping...")
time.sleep(3)

mux64 = mux64_chip(lpgbt, board="Readout Board") 
mux64.write_config()

master_id = 2
slave_address = 0x70
reg_address_width = 2
i2c_write = partial(
    lpgbt.i2c_master_write,
    master_id=master_id,          # e.g. 0, 1, or 2
    slave_address=slave_address,  # address of slave lpgbt
    reg_address_width=reg_address_width,      
    timeout=10                    # constant timeout
)

i2c_read = partial(
    lpgbt.i2c_master_read,
      master_id = master_id, 
      slave_address = slave_address, # for slave lpgbt`
      read_len = 1,
      reg_address_width = reg_address_width,
)

test_read = i2c_read(reg_address=0x0)
print("Test Read Successfull", test_read)

# lpgbt.i2c_master_reset(0)
# import time
# time.sleep(3)
# lpgbt.i2c_master_reset(0)
# Run Powerup like tamalero

i2c_write(reg_address=0x036, data=0x0)
i2c_write(reg_address=0x0fb, data=0x6)

print("reading rom reg, should be 0xa6")
val = i2c_read(reg_address=0x1d7)
print(val)
print(hex(val[0]))

#     If fails, use the registers below, also check what the CSV is setting
# maybe it is setting some registers it is not supposed to.

# Important registers to read:
    # I2CM2CTRL:    https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#x199-i2cm2ctrl
    #    => Tamalero sets it to be 0x6
    # I2CM2TRANCNT: https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#reg-i2cm2trancnt
    #    => This lets you knowo how many transactions were successful
    # I2CM2STATUS:  https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#reg-i2cm2status
    #    => a bunch of status registers regarding the transaction


