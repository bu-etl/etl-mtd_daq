from ..utils.timer import timer_decorator
import time
from ..controllers.lpgbt_controller import *
import argparse
import logging
import sys


@timer_decorator(message='lpgbt initialization', unit='ms')
def lpgbt_main(asic_name,
               cc_name,
               read_length=1,
               address="0x1d9",
               connection=None):

    # get a logger for lpGBT library logging
    lpgbt_logger = logging.getLogger("lpgbt")

    # Use configuration from database
    lpgbt = lpgbt_chip(asic_name, cc_name, logger=lpgbt_logger, connection=connection)

    '''
    ETL ADDITIONS START
    '''
    # set pin 8 as an output
    # 0000 0001 0000 0000
    # 0001 0000 0000 0000
    # 1000 0000 0000 0000
    lpgbt.lpgbt_cont_.set_multiwrite(False)

    print("#################")
    print("SETTING DIRECTION")
    print("#################\n")

    pin = 0x8000
    lpgbt.gpio_set_dir(pin)
    for i in range(10):
        print("setting low")
        lpgbt.gpio_set_out(0x0)
        time.sleep(5)
        print("setting high")
        lpgbt.gpio_set_out(pin)
        time.sleep(5)

    '''
    ETL ADDTIONS END
    '''
    # print("initializing lpGBT")
    # lpgbt.init_lpgbt()

    # print("0x{0:x}".format(
    #     lpgbt.lpgbt_cont_.read_lpgbt_regs(int(address, 0), read_length)[0])
    # )


if __name__ == "__main__":
    start = time.time()

    parser = argparse.ArgumentParser(description='lpgbt controller')
    parser.add_argument('-name', dest="asic_name",
                        help="LPGBT0 or LPGBT1 (default LPGBT0)",
                        required=False, default="LPGBT0")
    parser.add_argument('-cc', dest="cc_name",
                        help="Name of the CC this chip belongs to (e.g. CC3_T2)",
                        required=False)
    parser.add_argument('-length', dest="read_length", type=int,
                        default=1, help="length of the read array (default 1)")
    parser.add_argument('-addr', dest="address", default="0x1d9",
                        help="Register address (default \"0x1d9\")")

    parser.add_argument("-connection", default=None,
                        help="hls connection file, it gives the address to the serenity")
    
    args = parser.parse_args()

    lpgbt_main(args.asic_name,
               args.cc_name,
               args.read_length,
               args.address,
               connection=args.connection)
