import time
import sys
from lpgbt_control_lib import LpgbtV1
import emp
import uhal
import logging
print(emp.__file__)

# make sure to change in db:
# lpgbt = LpgbtV1(
#     "Master LPGBT",
#     connection="~/mtd-EMP_CONTROLLER-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml",
#     link=4,
#     lpgbt_address="0x73"
# )
logger = logging.getLogger("lpgbt")
con_man = uhal.ConnectionManager(
    "file://~/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml")
hw_int = uhal.HwInterface(con_man.getDevice("x0"))
EMP_CONTROLLER = emp.Controller(hw_int)
LPGBT_ADDR = 0x73
LINK=4
EMP_CONTROLLER.getDatapath().selectLink(LINK)

def write_lpgbt_regs(reg_addr, reg_vals:list):

    if not hasattr(reg_vals, "__len__"):
        reg_vals = [reg_vals]

    print("grabbing link")
    EMP_CONTROLLER.getDatapath().selectLink(LINK)
    print("grabbing sccic")
    sccic = EMP_CONTROLLER.getSCCIC()
    time.sleep(1)
    print("writing")
    # for reg_val in reg_vals:
    #     sccic.icWrite(reg_addr, reg_val, LPGBT_ADDR)
    try:
        sccic.icWriteBlock(reg_addr, reg_vals, LPGBT_ADDR)
    except Exception as e:
        print("icWriteBlock failed")
    time.sleep(1)

def read_lpgbt_regs(reg_adddr, read_len):
    raise NotImplementedError("This is bad.")

lpgbt = LpgbtV1(logger=logger)
lpgbt.register_comm_intf(
            name="IC",
            write_regs = write_lpgbt_regs,
            read_regs = read_lpgbt_regs,
            default=True
        )
time.sleep(1)
EMP_CONTROLLER.getSCC().reset()

time.sleep(1)
# reg_addr = lpgbt.decode_reg_addr(lpgbt.CHIPCONFIG)
# mask = lpgbt.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT.bit_mask
# sccic = EMP_CONTROLLER.getSCCIC()
# sccic.icInvertLink(reg_addr, mask, int(LPGBT_ADDR, 16))

# set pin 8 as an output
# 0000 0001 0000 0000
print("#################")
print("SETTING DIRECTION")
print("#################\n")


write_lpgbt_regs(0x053, 0x1)
# lpgbt.gpio_set_dir(0xFFFF)
time.sleep(5)
print("setting high")
write_lpgbt_regs(0x055, 0x1)
# lpgbt.gpio_set_out(0x100)
time.sleep(10)
print("setting low")
write_lpgbt_regs(0x055, 0x0)
# lpgbt.gpio_set_out(0x0)

# set pin 8 as high
# 0000 0001 0000 0000
# print("*************SETTING HIGH************")
# lpgbt.gpio_set_out(0x100)
# time.sleep(10)
# print("SETTING LOW")
# time.sleep(5)

#print(lpgbt.gpio_get_out())