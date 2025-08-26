"""
Authors: Naomi Gonzalez and Hayden Swanson

Description:
Control code for ETROC ASIC used in an ETL Module whose main purpose is to convert
Analog signal from sensors to digital signal.
"""

from .lpgbt_controller import lpgbt_chip
from ..utils.Configure_from_DB import etl_asic_config_from_db
from dataclasses import dataclass
from .etroc_registers import PeriReg, PixReg
import time
from functools import partial
from collections.abc import Callable
import numpy as np
from collections import UserList

class PixMatrix(UserList):
    def __init__(self, pixels):
        super().__init__(pixels)

    def write(self, register: int | str | PixReg, value:int):
        ...

@dataclass
class Pixel:
    row: int 
    col: int
    i2c_read: Callable
    i2c_write: Callable

    def __init__(self, i2c_read: Callable, i2c_write: Callable, row: int, col: int):
        self.row = row
        self.col = col
        self.i2c_read = i2c_read
        self.i2c_write = i2c_write


    def write(self, register: int | str | PixReg, value: int):
        """
        Write to ETROC pixel register through I2C Bus

        register: ETROC pixel register name(str) or pixel register number(int)
        value: value to write to a specific ETROC pixel register
        """
        if isinstance(register, int):
            reg = self.full_address(adr=register)
            self.i2c_write(reg_address=reg, data=value)
            return
        elif isinstance(register, str):
            reg = PixReg[register]
        elif isinstance(register, PixReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        for adr, val in zip(reg.addresses, reg.split_value(value)):
            full_addr = self.full_address(adr, is_status_reg = True)
            self.i2c_write(reg_address=full_addr, data=val)


    def read(self, register: int | str) -> int:
        """
        Reads from ETROC pixel register through I2C Bus

        register: ETROC pixel register name(str) or pixel register number(int)
        """
        if isinstance(register, int):
            reg =  self.full_address(adr=register)
            return self.i2c_read(reg_address=reg)
        elif isinstance(register, str):
            reg = PixReg[register]
        elif isinstance(register, PixReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        values = []
        for adr in reg.addresses:
            full_addr = self.full_address(adr, is_status_reg = True)            
            values.append(self.i2c_read(reg_address = full_addr)[0])
        return reg.merge_values(values)
    

    def auto_threshold_scan(self, timeout = 5):
        
        self.write(PixReg.CLKEn_THCal, 1)
        self.write(PixReg.Bypass_THCal, 0)
        self.write(PixReg.BufEn_THCal, 1)
        self.write(PixReg.RSTn_THCal, 0) # Check with Murtaza: Needed?
        self.write(PixReg.RSTn_THCal, 1) # Check with Murtaza: Needed?
        self.write(PixReg.ScanStart_THCal, 1)
        time.sleep(0.1)
        self.write(PixReg.ScanStart_THCal, 0)
        
        done = False
        start_time = time.time()
        timed_out = False
        while not done:
            done = True
            try:
                done = self.read(PixReg.ScanDone)
                print(f"ScanDone returned: {done}")
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

    def full_address(self, adr: int, 
                    broadcast:bool = False, 
                    is_status_reg:bool = False):
        """
        Construct a full ETROC register address by encoding address components into bit fields
        
        Address for in=pixel I2C access (see table 10 on page 48 of ETROC2 manual):
        - Bits 0-4:   In pixel register address
        - Bits 5-8:   Row address (0-15)
        - Bits 9-12:  Column address (0-15) 
        - Bit 13:     0: direct message to a specific pixel, 1: brodcast to all pixels
        - Bit 14:     1: status, 0: configuration
        - Bit 15:     1: pixel matrix, 0: periphery
        

        adr: Base register address (0-31)
        row: Pixel row coordinate (0-15, default: 0)
        col: Pixel column coordinate (0-15, default: 0)
        broadcast: Enable broadcast mode to all pixels (default: False)
        is_status_reg: Address targets a status register (default: False)
        is_pixel_reg: Address targets a pixel register (default: False)

        Returns -> Complete 16-bit encoded address for ETROC register access
        """
        is_pixel_reg = True
        return adr | self.row << 5 | self.col << 9 | broadcast << 13 | is_status_reg <<14 | is_pixel_reg << 15


# ---------------------------------------------------------------
# Main ETROC Chip Class
# ---------------------------------------------------------------
class etroc_chip:
    addr_i2c: int
    lpgbt: lpgbt_chip
    connected: bool
    vref: bool
    pixels: list[list[Pixel]]


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

        self.pixels = [
            [Pixel(self.i2c_read, self.i2c_write, row, col) for col in range(16)] for row in range(16)]
        
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
            print(test)
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
        for row in range(16):
            for col in range(16):
                print(f"Configuring pixel: {row=}, {col=}")
                pix = self.pixels[row][col]
                pix.write(PixReg.L1Adelay, 0x01f5)

                # opening TOA / TOT / Cal windows
                pix.write(PixReg.upperTOA, 0x3ff)
                pix.write(PixReg.lowerTOA, 0)
                pix.write(PixReg.upperTOT, 0x1ff)
                pix.write(PixReg.lowerTOT, 0)
                pix.write(PixReg.upperCal, 0x3ff)
                pix.write(PixReg.lowerCal, 0)

                # Configuring the trigger stream
                pix.write(PixReg.disTrigPath, 1)
                pix.write(PixReg.upperTOATrig, 0x3ff)
                pix.write(PixReg.lowerTOATrig, 0)
                pix.write(PixReg.upperTOTTrig, 0x1ff)
                pix.write(PixReg.lowerTOTTrig, 0)
                pix.write(PixReg.upperCalTrig, 0x3ff)
                pix.write(PixReg.lowerCalTrig, 0)

        self.reset()


    # TODO: change this to set/getter
    def power_Vref(self, val: bool):
        """
        Power up/down internal VREF on ETROC
        """
        self.write("VRefGen_PD", val)


    def write(self, register: int | str | PeriReg, value: int):
        """
        Write to ETROC register through lpGBT I2C Bus

        register: ETROC register name(str) or register number(int)
        value: value to write to a specific ETROC register
        """
        if isinstance(register, int):
            self.i2c_write(reg_address=register, data=value)
            return
        elif isinstance(register, str):
            reg = PeriReg[register]
        elif isinstance(register, PeriReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        for adr, val in zip(reg.addresses, reg.split_value(value)):
            full_addr = self.full_address(adr, is_status_reg=reg.is_status_reg)
            self.i2c_write(reg_address=full_addr, data=val)


    def read(self, register: int | str) -> int:
        """
        Reads from ETROC register through lpGBT I2C Bus

        register: ETROC register name(str) or register number(int)
        """

        if isinstance(register, int):
            return self.i2c_read(reg_address=register)
        elif isinstance(register, str):
            reg = PeriReg[register]
        elif isinstance(register, PeriReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")
    
        values = []
        for adr in reg.addresses:
            full_addr = self.full_address(adr, is_status_reg=reg.is_status_reg)
            values.append(self.i2c_read(reg_address=full_addr)[0])
        return reg.merge_values(values)


    def run_threshold_scan(self):
        """
        Preform threshold scan on full ETROC chip (all pixels)
        """
        for row in range(16):
            for col in range(16):
                pix = self.pixels[row][col]

                pix.write(PixReg.Bypass_THCal, 1)
                pix.write(PixReg.disDataReadout, 1)
                pix.write(PixReg.enable_TDC, 0)
                pix.write(PixReg.DAC, 1023)
                pix.write(PixReg.TH_offset, 63)

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

    def full_address(self, adr: int, is_status_reg: bool = False) -> int:
        """
        Construct a full ETROC periphery register address based on table 11 in ETROC2 Manual.
        
        Periphery addressing scheme:
        - Configuration: 0x0000 - 0x001F (addresses 0-31)
        - Status:        0x0100 - 0x010F (addresses 0-15 with status flag)
        - SEU Counter:   0x0120 - 0x0123 (addresses 32-35 with status flag)
        - Magic number:  0x0020 (address 32 configuration)
        
        The address format uses:
        - Bits 0-7:   Base register address
        - Bit 8:      Status register flag (1 for status, 0 for configuration)
        - Bits 9-15:  Reserved (0)
        
        adr: Base register address 
        is_status_reg: True for status registers, False for configuration
        
        Returns -> Complete 16-bit encoded address for ETROC periphery register access
        """
        if is_status_reg:
            return 0x0100 | adr
        else:
            return adr



