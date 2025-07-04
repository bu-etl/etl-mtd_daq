import time
import sys
from lpgbt_control_lib import LpgbtV1
import emp
import uhal
import logging
print(emp.__file__)

if "/home/cmx/mtd-emp-toolbox/chip_reformat/src" in sys.path:
    sys.path.remove("/home/cmx/mtd-emp-toolbox/chip_reformat/src")

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
    values = self.SCCIC.icReadBlock(
        addr, nwords, lpgbt_addr)
    values = [value & 0xff for value in values]


lpgbt = LpgbtV1(logger=logger)
lpgbt.register_comm_intf(
            name="IC",
            write_regs = write_lpgbt_regs,
            read_regs = read_lpgbt_regs,
            default=True
        )
time.sleep(1)
EMP_CONTROLLER.getSCC().reset()

for i in range(50):
    #lpgbt = lpgbt_chip("LPGBT0", "CC1_T2")

    # TOGGLE DOWNLINK INTO UPLINK
    try:
        write_lpgbt_regs(0x118, 0xC0)
    except Exception as e:
        print(e)
    time.sleep(0.1)
    try:
        write_lpgbt_regs(0x118, 0)
    except Exception as e:
        print(e)

    # HIGH SPEED DATA OUT INVERT, 
    reg_addr = lpgbt.decode_reg_addr(lpgbt.CHIPCONFIG)
    mask = lpgbt.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT.bit_mask
    sccic = EMP_CONTROLLER.getSCCIC()
    try:
        sccic.icInvertLink(reg_addr, mask, LPGBT_ADDR)
    except Exception as e:
        print(e)

    try:
        lpgbt.config_done() #POWERUP2
    except Exception as e:
        print(e)
    time.sleep(1)
    # should have this method because it inherits from LpgbtV1 which inherits from Lpgbt
    print("trying to read ROMREG")
    try:
        v1 = lpgbt.read_reg(0x1c5)
        print("SUCCESSSS v1 is", v1)
        print("should be 0xa6")
        break
    except Exception as e:
        print(e)
    
    print("trying again...")
    time.sleep(0.3)
