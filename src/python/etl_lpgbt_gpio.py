import time
import sys
from ..controllers.lpgbt_controller import *

# make sure to change in db:
# 0x73
# 0x60
# 0x70
lpgbt = lpgbt_chip("Master LPGBT")

# set pin 8 as an output
# 0000 0001 0000 0000
lpgbt.gpio_set_dir(0x100)

# set pin 8 as high
# 0000 0001 0000 0000
lpgbt.gpio_set_out(0x100)
time.sleep(10)
lpgbt.gpio_set_out(0x0)

print(lpgbt.gpio_get_out())