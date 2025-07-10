'''
Info: When connecting Frontend Electronics to Serenity trying to use MTD software
to control a GPIO pin on the lpGBT
'''


import time
import sys
from ..controllers.lpgbt_controller import *

# make sure to change in db:
# 0x73
# 0x60
# 0x70
lpgbt = lpgbt_chip(
    "Master LPGBT",
    connection="~/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml",
    link=4,
    lpgbt_address="0x73"
    )

# set pin 8 as an output
# 0000 0001 0000 0000
print("#################")
print("SETTING DIRECTION")
lpgbt.gpio_set_dir(0xFFFF)
print("#################\n")
time.sleep(1)
print("setting low")
lpgbt.gpio_set_out(0x0)


# set pin 8 as high
# 0000 0001 0000 0000
# print("*************SETTING HIGH************")
# lpgbt.gpio_set_out(0x100)
# time.sleep(10)
# print("SETTING LOW")
# time.sleep(5)

#print(lpgbt.gpio_get_out())