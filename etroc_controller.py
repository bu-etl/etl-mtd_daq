"""
Authors: Naomi Gonzalez and Hayden Swanson

Description:
Control code for ETROC ASIC used in an ETL Module whose main purpose is to convert
Analog signal from sensors to digital signal.
"""

from .lpgbt_controller import lpgbt_chip
from ..utils.Configure_from_DB import etl_asic_config_from_db
from dataclasses import dataclass

@dataclass
class Pixel:

    # Hayden
    write()

    # Hayden
    read()


class etroc_chip:
    addr_i2c: int
    lpgbt: lpgbt_chip
    connected: bool
    vref: bool


    def __init__(self, lpgbt: lpgbt_chip, address_i2c: int, ):
        """
        Checks connectivity then writes initial configuration of ETROC 
        """
        self.lpgbt = lpgbt
        self. addr_i2c = address_i2c
        self.i2c_write = partial(
            self.lpgbt.i2c_master_write,
            master_id=2,          
            slave_address=address_i2c,  
            reg_address_width=8,      
            timeout=10                    
        )
        self.is_connected()

        # HAYDEN
        # initialize pixel matrix
        
        self.DAC_min = 600 #mV
        self.DAC_max = 1000 #mV
        self.DAC_step = 400/2**10

        self.reset(hard = True)
        self.power_Vref(True) 
        self.config()


    # TODO: change this to set/getter
    def is_connected():
        """
        Check ETROC connectivity through reading first reg and verifying
        value is 0x2c
        """
        try:
            test = self.read(0x0)
            self.connected = True if test==0x2c else False
        except TimeoutError:
            self.connected = False
        return self.connected


    def reset(self, hard=False):
        if hard:
            self.lpgbt.write_gpio_output("RESET1",0)
            sleep(0.05)
            self.lpgbt.write_gpio_output("RESET1",1)
        else:
            self.write("asyResetGlobalReadout", 0)
            sleep(0.05)
            self.write("asyResetGlobalReadout", 1)


    def config(self):
        if not self.is_connected():
            raise ConnectionError(f"ETROC addr: {self. addr_i2c} Not Connected")

        self.reset()
        self.write("singlePort", 0)         # use both ports
        self.write("mergeTriggerData", 1)   # merge trigger and data
        self.write("disScrambler", 1)       # disable scrambler
        self.write("serRateRight", 0)       # right port 320Mbps rate
        self.write("serRateLeft", 0)        # left port 320Mbps rate

        for ...
            for ...
                self.pixel[i,j].write("qnji", 0)


    # TODO: change this to set/getter
    def power_Vref(self, val: bool):
        self.write("VRefGen_PD", val)

    # HAYDEN
    # Implement either number or name of reg
    def write(self, register, value):
        print("writing")


        # if they give me number
        reg = PheriphralReg[register]
        for adr, val in zip(reg.addresses, reg.split_value(value):
            full_address = stuff & adr
            self.i2c_write(...)

    # HAYDEN
    def read(self, reg):
        print("reading")

    # HAYDEN
    def autothreshold_scan(self):



