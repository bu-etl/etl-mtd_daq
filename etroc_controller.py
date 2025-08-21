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


class etroc_chip:

    def __init__(self, lpgbt: lpgbt_chip):
        print("init")

        # Check Connectivity: Read first ETROC register (0x2c)
        # Load register names and address (read csv)
        # initialize pixel matrix
        
        self.DAC_min = 600 #mV
        self.DAC_max = 1000 #mV
        self.DAC_step = 400/2**10

        # Perform hard reset
        # Power up vref 
        # config

    def config(self):
        print("config")

    def reset(self, hard=False):
        print("reset")
        `
    def power_up_Vref(self):
        print("power up")

    def power_down_Vref(self):
        print("power down")


    # Implement either number or name of reg
    def write(self, reg, value):
        print("writing")

    def read(self, reg):
        print("reading")

    def autothreshold_scan(self):




