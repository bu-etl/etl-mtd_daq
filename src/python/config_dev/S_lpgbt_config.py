'''
Info: Performs full lpgbt configuration from the database on the Master lpGBT
'''

import time
import sys
from ..controllers.lpgbt_controller import *

# make sure to change in db:
# 0x73
# 0x60
# 0x70
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lpgbt")

lpgbt = lpgbt_chip(
    "Master LPGBT",
    "Readout Board",
    connection="~/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml",
    link=4,
    # lpgbt_address="0x73"
    )

lpgbt.init_lpgbt()


lpgbt.config["configurations"]["PSCLK"] = {
    f"frequency_ps_{i}": 0 for i in range(6)
}

for rate in range(6):
    lpgbt.config["configurations"]["EPTX"][f"data_rate_gr_{rate}"] = 3
    lpgbt.config["configurations"]["EPTX"][f"mirror_gr_{rate}"] = True
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_width_gr_{rate}"] = 0
    lpgbt.config["configurations"]["EPTX"][f"invert_gr_{rate}"] = False
    lpgbt.config["configurations"]["EPTX"][f"drive_strength_gr_{rate}_ch_0"] = 3
    lpgbt.config["configurations"]["EPTX"][f"drive_strength_gr_{rate}_ch_1"] = 3
    lpgbt.config["configurations"]["EPTX"][f"drive_strength_gr_{rate}_ch_2"] = 3
    lpgbt.config["configurations"]["EPTX"][f"drive_strength_gr_{rate}_ch_3"] = 3

    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_mode_gr_{rate}_ch_0"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_mode_gr_{rate}_ch_1"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_mode_gr_{rate}_ch_2"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_mode_gr_{rate}_ch_3"] = 0

    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_strength_gr_{rate}_ch_0"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_strength_gr_{rate}_ch_1"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_strength_gr_{rate}_ch_2"] = 0
    lpgbt.config["configurations"]["EPTX"][f"pre_emphasis_strength_gr_{rate}_ch_3"] = 0

lpgbt.setup_ELINKS()

# self.eptx_ec_setup()  # FDG why is this needed? what parameters are taken?
# self.eprx_ec_setup()
# lpgbt.setup_EPTX()
# lpgbt.setup_EPRX()
# lpgbt.setup_eclk_frequency()
# lpgbt.setup_psclk_frequency()

print("################ READING LPGBT REGISTERS ########################")
print(lpgbt.read_reg(0x1d7))
lpgbt.log_regs()
