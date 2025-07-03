from tamalero.utils import get_kcu
from time import sleep
# test

def wr_adr(kcu, adr, data):
    kcu.toggle_dispatch()
    #kcu.write_node("READOUT_BOARD_%d.SC.TX_GBTX_ADDR" % rb, 115)
    kcu.write_node("READOUT_BOARD_0.SC.TX_REGISTER_ADDR", adr)
    kcu.write_node("READOUT_BOARD_0.SC.TX_DATA_TO_GBTX", data)
    kcu.action("READOUT_BOARD_0.SC.TX_WR")
    kcu.action("READOUT_BOARD_0.SC.TX_START_WRITE")
    kcu.dispatch()


print("Getting kcu...")
kcu = get_kcu("192.168.0.10")
print("Obtained kcu")
#kcu.write_node("READOUT_BOARD_0.SC.FRAME_FORMAT", 1)
#print("Set Frame Format for lpgbt v1")

# toggles downlink into uplink
# wr_adr(0x128, 0xC0) # https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#x128-uldatasource0
# sleep(0.01)
# wr_adr(0x128, 0) # https://lpgbt.web.cern.ch/lpgbt/v1/registermap.html#x128-uldatasource0

##
### High Speed Data Invert
##
# print("Setting high speed data invert")
# wr_adr(kcu,0x036, 0x80)

##
### GPIO PINS
##
print("setting gpio as output")
wr_adr(kcu,0x053, 0x1) # set direction to out, PIOOUTH

print("Setting high")
wr_adr(kcu,0x055, 0x1) # set high, PIOOutH
sleep(2)
print("setting low")
wr_adr(kcu,0x055, 0x0) # set low, PIOOutH

