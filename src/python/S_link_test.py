'''
Info: When connecting Frontend Electronics to Serenity trying to use Tamalero configuration 
steps to try to then attempt the first read of the lpGBT
'''

import time
import sys
from ..controllers.lpgbt_controller import *

if "/home/cmx/mtd-emp-toolbox/chip_reformat/src" in sys.path:
    sys.path.remove("/home/cmx/mtd-emp-toolbox/chip_reformat/src")

for i in [0,1]:
    for link in [0,1,2,3,4,5,6,7,8,9,10,11]:
        if i:
            send_link = link
        else:
            send_link = 4
        
        try:
            lpgbt = lpgbt_chip(
                "Master LPGBT", 
                link=send_link,
                connection="~/mtd-emp-toolbox/mtd-daq/lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/hls_connections.xml")
            lpgbt.lpgbt_cont_.set_multiwrite(False)    
            lpgbt.init_lpgbt()
            time.sleep(1)
            lpgbt.write_reg(0x03b, 0)
            lpgbt.write_reg(0x0f1, 0x50)
            lpgbt.write_reg(0x039, 0x7f)
            lpgbt.write_reg(0x037, 0)
            time.sleep(1)
        except Exception as e:
            print(f"Failed in init, {send_link=}, {link=}, {e}")
            continue
    
        for _ in range(50):
            try:
                print("Toggling downlink into uplink")
                time.sleep(0.01)
                lpgbt.write_reg(0x128, 0xC0)#0xC0
                time.sleep(0.1)
                lpgbt.write_reg(0x128, 0)
                # time.sleep(1)

                # HIGH SPEED DATA OUT INVERT, 
                reg_addr = lpgbt.decode_reg_addr(lpgbt.CHIPCONFIG)
                mask = lpgbt.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT.bit_mask
                lpgbt.lpgbt_cont_.lpgbt_com.set_link(reg_addr = reg_addr, mask = mask, lpgbt_addr = int(lpgbt.lpgbt_cont_.lpgbt_addr, 16))

                lpgbt.config_done() #POWERUP2
                time.sleep(0.01)
                # should have this method because it inherits from LpgbtV1 which inherits from Lpgbt

                print(f"attempting to read! ({send_link}, {link})")
                lpgbt.lpgbt_cont_.lpgbt_com.emp_cont.getDatapath().selectLink(link)
                time.sleep(0.1)
                v1 = lpgbt.read_reg(0x1d7)
                quit()

                # print("0x{0:x}".format(
                #     lpgbt.lpgbt_cont_.read_lpgbt_regs(int("0x1d9", 0), 1)[0])
                # )

                # print("v1 is", v1)
                # if v1 == 0xa6:
                #     break
                # else:
                #     print(f"trying again... it was read as: {v1}")
                #     time.sleep(0.3)
            except Exception as e:
                print(f"failed but gonna try again: {e}")
                lpgbt.lpgbt_cont_.lpgbt_com.reset_slow_control_logic()
