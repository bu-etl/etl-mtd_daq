"""
Authors: Naomi Gonzalez and Hayden Swanson

Description:
Control code for ETROC ASIC used in an ETL Module whose main purpose is to convert
Analog signal from sensors to digital signal.
"""

from .lpgbt_controller import lpgbt_chip
from ..utils.Configure_from_DB import etl_asic_config_from_db
from dataclasses import dataclass
from etroc_registers import PeriReg, PixReg
import time
from functools import partial
from collections.abc import Callable
import numpy as np

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

    # Hayden
    def write(self, register: int | str | PixReg, value: int):
        if isinstance(register, int):
            self.i2c_write(register, value)
            return
        elif isinstance(register, str):
            reg = PixReg[register]
        elif isinstance(register, PixReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        for adr, val in zip(reg.addresses, reg.split_value(value)):
            full_addr = self.full_address(adr, 
                                          row = self.row, 
                                          col = self.col, 
                                          is_status_reg = True)
            self.i2c_write(full_addr, val)

    # Hayden
    def read(self, register: int | str) -> int:
        if isinstance(register, int):
            return self.i2c_read(register)
        elif isinstance(register, str):
            reg = PixReg[register]
        elif isinstance(register, PixReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        values = []
        for adr in reg.addresses:
            full_addr = self.full_address(adr, 
                                          row = self.row, 
                                          col = self.col, 
                                          is_status_reg = True)            
            values.append(self.i2c_read(full_addr))
        return reg.merge_values(values)
    
    # Hayden
    def auto_threshold_scan(self, timeout = 3):
        
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

    def full_address(self, adr: int, 
                    row:int = 0, 
                    col:int = 0, 
                    broadcast:bool = False, 
                    is_status_reg:bool = False):
        """
        Construct a full ETROC register address by encoding address components into bit fields.
        
        Address for in=pixel I2C access (see table 10 on page 48 of ETROC2 manual):
        - Bits 0-4:   In pixel register address
        - Bits 5-8:   Row address (0-15)
        - Bits 9-12:  Column address (0-15) 
        - Bit 13:     0: direct message to a specific pixel, 1: brodcast to all pixels
        - Bit 14:     1: status, 0: configuration
        - Bit 15:     1: pixel matrix, 0: periphery
        
        Args:
            adr: Base register address (0-31)
            row: Pixel row coordinate (0-15, default: 0)
            col: Pixel column coordinate (0-15, default: 0)
            broadcast: Enable broadcast mode to all pixels (default: False)
            is_status_reg: Address targets a status register (default: False)
            is_pixel_reg: Address targets a pixel register (default: False)

        Returns:
            int: Complete 16-bit encoded address for ETROC register access
        """
        is_pixel_reg = True
        return adr | row << 5 | col << 9 | broadcast << 13 | is_status_reg <<14 | is_pixel_reg << 15


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
            master_id=2,          
            slave_address=address_i2c,  
            reg_address_width=8,      
            timeout=10                    
        )

        self.i2c_read = partial(
            lpgbt.i2c_master_read,
            master_id = 2, 
            slave_address = self.addr_i2c, # for slave lpgbt`
            read_len = 1,
            reg_address_width = 2,
        )

        self.is_connected()

        # HAYDEN
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
            self.connected = True if test==0x2c else False
        except TimeoutError:
            self.connected = False
        return self.connected


    def reset(self, hard=False):
        if hard:
            self.lpgbt.write_gpio_output("RESET1",0)
            time.sleep(0.05)
            self.lpgbt.write_gpio_output("RESET1",1)
        else:
            self.write("asyResetGlobalReadout", 0)
            time.sleep(0.05)
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


    # TODO: change this to set/getter
    def power_Vref(self, val: bool):
        self.write("VRefGen_PD", val)

    # HAYDEN
    def write(self, register: int | str | PeriReg, value: int):
        if isinstance(register, int):
            self.i2c_write(register, value)
            return
        elif isinstance(register, str):
            reg = PeriReg[register]
        elif isinstance(register, PeriReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")

        for adr, val in zip(reg.addresses, reg.split_value(value)):
            full_addr = self.full_address(adr, is_status_reg=reg.is_status_reg)
            self.i2c_write(full_addr, val)

    # HAYDEN
    def read(self, register: int | str) -> int:
        if isinstance(register, int):
            return self.i2c_read(register)
        elif isinstance(register, str):
            reg = PeriReg[register]
        elif isinstance(register, PeriReg):
            reg = register
        else:
            raise TypeError(f"Unsupported type for register {type(register)}")
    
        values = []
        for adr in reg.addresses:
            full_addr = self.full_address(adr, is_status_reg=reg.is_status_reg)
            values.append(self.i2c_read(full_addr))
        return reg.merge_values(values)

    # HAYDEN
    def run_threshold_scan(self):

        # broadcast later....
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
                pix = self.pixels[row][col]
                baselines[row][col], noisewidths[row][col] = pix.auto_threshold_scan()

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
        
        Args:
            adr: Base register address (0-255)
            is_status_reg: True for status registers, False for configuration (default: False)
        
        Returns:
            int: Complete 16-bit encoded address for ETROC periphery register access
            
        Examples:
            >>> full_address(0x10)  # Configuration register 16
            16  # 0x0010
            >>> full_address(0x05, is_status_reg=True)  # Status register 5
            261  # 0x0105
            >>> full_address(0x20, is_status_reg=True)  # SEU Counter base
            288  # 0x0120
        
        Note:
            Magic number register (0x20) should be accessed as configuration:
            full_address(0x20, is_status_reg=False) -> 0x0020
        """
        if is_status_reg:
            # Status registers: 0x0100 base + address offset
            return 0x0100 | adr
        else:
            # Configuration registers: direct address (0x0000 - 0x001F, 0x0020)
            return adr