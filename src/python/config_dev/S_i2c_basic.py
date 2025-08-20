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

from ..controllers.mux64_controller import mux64_chip

mux64 = mux64_chip(lpgbt, board="Readout Board") 
#mux64.write_config()


#before = lpgbt.i2c_master_read(
#  master_id = 0, # either 0, 1, 2, check what tamalero uses
#  slave_address = 0x60, # for slave lpgbt
#  read_len = 1,
#  reg_address_width = 1,
#  reg_address = 0x1d7
#)
#print(before)

lpgbt.i2c_master_reset(0)
import time
time.sleep(3)
lpgbt.i2c_master_reset(0)
# Run Powerup
reg_address = 0xfb # https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html?highlight=powerup2#x0fb-powerup2
lpgbt.i2c_master_write(
  master_id = 0, # either 0, 1, 2, check what tamalero uses
  slave_address = 0x60, # for slave lpgbt
  reg_address_width = 1, 
  reg_address = reg_address, 
  data = 0x6, # following tamalero
  timeout = 10
)

after = lpgbt.i2c_master_read(
  master_id = 0, # either 0, 1, 2, check what tamalero uses
  slave_address = 0x60, # for slave lpgbt`
  read_len = 1,
  reg_address_width = 1,
  reg_address = 0x1d9 # PUSMSTATUS https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#x1d9-pusmstatus
)
print(after)
