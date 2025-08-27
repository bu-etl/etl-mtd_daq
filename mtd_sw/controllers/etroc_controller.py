"""
Authors: Naomi Gonzalez and Hayden Swanson

Description:
Control code for ETROC ASIC used in an ETL Module whose main purpose is to convert
Analog signal from sensors to digital signal.
"""

from .lpgbt_controller import lpgbt_chip
from ..utils.Configure_from_DB import etl_asic_config_from_db
from dataclasses import dataclass
from .etroc_registers import PeriReg, PixReg, validate_is_pixel
import time
from functools import partial
from collections.abc import Callable
import numpy as np
from collections import UserList

@dataclass
class Pixel:
    row: int 
    col: int
    etroc: etroc_chip

    def __init__(self, etroc: etroc_chip, row: int, col: int):
        self.row = row
        self.col = col
        self.etroc = etroc

    def write(self, register:str|PixReg|PeriReg, value: int):
        self.etroc.write(register, value, row=self.row, col=self.col)
        
    def read(self, register:str|PixReg|PeriReg) -> int:
        """
        Reads from ETROC pixel register through I2C Bus

        register: ETROC pixel register name(str) or pixel register number(int)
        """
        return self.etroc.read(register)
    
    def auto_threshold_scan(self, timeout = 5):
        
        self.write(PixReg.CLKEn_THCal, 1)
        self.write(PixReg.Bypass_THCal, 0)
        self.write(PixReg.BufEn_THCal, 1)
        self.write(PixReg.RSTn_THCal, 0) # Check with Murtaza: Needed?
        self.write(PixReg.RSTn_THCal, 1) # Check with Murtaza: Needed?
        self.write(PixReg.ScanStart_THCal, 1)
        self.write(PixReg.ScanStart_THCal, 0)
        
        done = False
        start_time = time.time()
        timed_out = False
        while not done:
            done = True
            try:
                done = self.read(PixReg.ScanDone)
            except:
                print("ScanDone read failed.")
            # time.sleep(0.01) # Murtaza: Increase (before 0.001)
            time.sleep(0.01) # Murtaza: Increase (before 0.001)
            if time.time() - start_time > timeout:
                print(f"Auto threshold scan timed out for pixel {self.row=}, {self.col=}")
                timed_out = True
                break

        noise_width = self.read("NW")
        baseline = self.read("BL")
        self.write(PixReg.Bypass_THCal, 1)
        # self.write('DAC', min(baseline+noise_width, 1023))

        # From Murtaza: DAC/TH_offset to the maximum, turn off cal clk and buffer
        self.write(PixReg.DAC, 1023)
        self.write(PixReg.TH_offset, 63 )
        self.write(PixReg.CLKEn_THCal, 0)
        self.write(PixReg.BufEn_THCal, 0)

        return baseline, noise_width

@dataclass
class PixMatrix(UserList):
    """
    This classed is used for an alternative api for broadcasting. For example:

    etroc = etroc_chip(...)
    etroc.pixels.write("your_reg")
    """
    def __init__(self, pixels):
        self.pixels = pixels
        super().__init__(pixels)

    def write(self, register:str|PixReg|PeriReg, value:int) -> None:
        etroc = self.pixels[0][0].etroc
        etroc.write(register, value, broadcast=True)

# ---------------------------------------------------------------
# Main ETROC Chip Class
# ---------------------------------------------------------------
class etroc_chip:
    addr_i2c: int
    lpgbt: lpgbt_chip
    connected: bool
    vref: bool
    pixels: PixMatrix[list[Pixel]]


    def __init__(self, lpgbt: lpgbt_chip, address_i2c: int):
        """
        Checks connectivity then writes initial configuration of ETROC 
        """
        self.lpgbt = lpgbt
        self. addr_i2c = address_i2c
        self.i2c_write = partial(
            self.lpgbt.i2c_master_write,
            master_id=1,          
            slave_address=address_i2c,  
            reg_address_width=2,      
            timeout=10                    
        )

        self.i2c_read = partial(
            lpgbt.i2c_master_read,
            master_id = 1, 
            slave_address = self.addr_i2c, 
            read_len = 1,
            reg_address_width = 2,
            timeout=10
        )
        
        print("Connecting...")

        self.is_connected()
        print("ETROC Connection status:", self.connected)

        self.pixels = PixMatrix([
            [Pixel(self.i2c_read, self.i2c_write, row, col) for col in range(16)] for row in range(16)])
        
        self.DAC_min = 600 #mV
        self.DAC_max = 1000 #mV
        self.DAC_step = 400/2**10

        self.reset(hard = True)
        self.power_Vref(True) 
        self.config()


    # TODO: change this to set/getter
    def is_connected(self):
        """
        Check ETROC connectivity through reading first reg and verifying
        value is 0x2c
        """
        try:
            test = self.read(0x0)
            self.connected = True if test==[0x2c] else False
        except TimeoutError:
            self.connected = False
        return self.connected


    def reset(self, hard=False):
        """
        Issues Hard or Soft Reset to ETROC chip
        """
        if hard:
            self.lpgbt.write_gpio_output("RESET1",0)
            time.sleep(0.05)
            self.lpgbt.write_gpio_output("RESET1",1)
        else:
            self.write("asyResetGlobalReadout", 0)
            time.sleep(0.05)
            self.write("asyResetGlobalReadout", 1)


    def config(self):
        """
        Writes Initial ETL Default Configuration for ETROC registers
        """
        if not self.connected:
            raise ConnectionError(f"ETROC addr: {hex(self.addr_i2c)} Not Connected")

        self.reset()
        self.write(PeriReg.singlePort, 0)         # use both ports
        self.write(PeriReg.mergeTriggerData, 1)   # merge trigger and data
        self.write(PeriReg.disScrambler, 1)       # disable scrambler
        self.write(PeriReg.serRateRight, 0)       # right port 320Mbps rate
        self.write(PeriReg.serRateLeft, 0)        # left port 320Mbps rate

        # TODO: Write Chip ID to EFUSE

        # configuration as per discussion with ETROC2 developers
        # -> values from Tamalero ETROC.py
        self.write(PeriReg.onChipL1AConf, 0) 
        self.write(PeriReg.PLL_ENABLEPLL, 1)
        
        ## Pixel Configurations
        self.pixels.write(PixReg.L1Adelay, 0x01f5)
        # opening TOA / TOT / Cal windows
        self.pixels.write(PixReg.upperTOA, 0x3ff)
        self.pixels.write(PixReg.lowerTOA, 0)
        self.pixels.write(PixReg.upperTOT, 0x1ff)
        self.pixels.write(PixReg.lowerTOT, 0)
        self.pixels.write(PixReg.upperCal, 0x3ff)
        self.pixels.write(PixReg.lowerCal, 0)

        # Configuring the trigger stream
        self.pixels.write(PixReg.disTrigPath,  1)
        self.pixels.write(PixReg.upperTOATrig, 0x3ff)
        self.pixels.write(PixReg.lowerTOATrig, 0)
        self.pixels.write(PixReg.upperTOTTrig, 0x1ff)
        self.pixels.write(PixReg.lowerTOTTrig, 0)
        self.pixels.write(PixReg.upperCalTrig, 0x3ff)
        self.pixels.write(PixReg.lowerCalTrig, 0)

        self.reset()

    # TODO: change this to set/getter
    def power_Vref(self, val: bool):
        """
        Power up/down internal VREF on ETROC
        """
        self.write("VRefGen_PD", val)    

    def write(self, register: str|PeriReg|PixReg, value:int, row:int=None, col:int=None, broadcast:bool=False):
        """
        Write to ETROC register through lpGBT I2C Bus

        register: ETROC register name(str) or register number(int)
        value: value to write to a specific ETROC register
        """
        if isinstance(register, int):
            raise TypeError("You attempted to pass an integer for the register in write. If you want to write to a specific address please use the i2c_write and i2c_read methods of this class.")

        is_pixel = validate_is_pixel(row, col)
        
        if isinstance(register, str):
            register = PixReg[register] if is_pixel else PeriReg[register]

        full_addresses = register.full_addresses(row=row, col=col, broadcast=broadcast)
        for adr, val in zip(full_addresses, register.split_value(value)):
            self.i2c_write(reg_address=adr, data=val)

    def read(self, register: str|PeriReg|PixReg, row:int=None, col:int=None) -> int:
        """
        Reads from ETROC register through lpGBT I2C Bus

        register: ETROC register name(str) or register number(int)
        """

        if isinstance(register, int):
            raise TypeError("You attempted to pass an integer for the register in write. If you want to write to a specific address please use the i2c_write and i2c_read methods of this class.")

        is_pixel = validate_is_pixel(row, col)
        
        if isinstance(register, str):
            register = PixReg[register] if is_pixel else PeriReg[register]
        
        values = []
        for adr in register.full_addresses(row=row, col=col):
            values += self.i2c_read(reg_address=adr)
        return register.merge_values(values)

    def run_threshold_scan(self):
        """
        Preform threshold scan on full ETROC chip (all pixels)
        """
        self.pixels.write(PixReg.Bypass_THCal, 1)
        self.pixels.write(PixReg.disDataReadout, 1)
        self.pixels.write(PixReg.enable_TDC, 0)
        self.pixels.write(PixReg.DAC, 1023)
        self.pixels.write(PixReg.TH_offset, 63)

        baselines = np.empty([16, 16])
        noisewidths = np.empty([16, 16])

        for row in range(16):
            for col in range(16):
                print(f"Threshold scan on pixel: {row=},{col=}")
                pix = self.pixels[row][col]
                bl, nw = pix.auto_threshold_scan()
                baselines[row][col], noisewidths[row][col] = bl, nw
                print(bl, nw)

        self.write(PixReg.disDataReadout, 0)
        self.write(PixReg.disTrigPath, 0)
        self.write(PixReg.enable_TDC, 1)

        return baselines, noisewidths
