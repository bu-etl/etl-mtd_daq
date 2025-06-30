import time
import sys
from ..controllers.lpgbt_controller import *

for i in range(50):
    lpgbt = lpgbt_chip("Master LPGBT")
    #lpgbt = lpgbt_chip("LPGBT0", "CC1_T2")


    # TOGGLE DOWNLINK INTO UPLINK
    lpgbt.write_reg(0x118, 0xC0)
    time.sleep(0.1)
    lpgbt.write_reg(0x118, 0)

    # HIGH SPEED DATA OUT INVERT, 
    lpgbt.lpgbt_cont_.set_multiwrite(False) #write immediately to register
    reg_addr = lpgbt.decode_reg_addr(lpgbt.CHIPCONFIG)
    mask = lpgbt.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT.bit_mask
    lpgbt.lpgbt_cont_.lpgbt_com.set_link(reg_addr = reg_addr, mask = mask, lpgbt_addr = int(lpgbt.lpgbt_cont_.lpgbt_addr, 16))
    lpgbt.lpgbt_cont_.set_multiwrite(True)  #cache writings until the first read is done

    lpgbt.config_done() #POWERUP2
    time.sleep(0.1)
    # should have this method because it inherits from LpgbtV1 which inherits from Lpgbt
    v1 = lpgbt.read_reg(0x1c5)

    print("v1 is", v1)
    if v1 == 0xa6:
        break
    else:
        print("trying again...")
        time.sleep(0.3)