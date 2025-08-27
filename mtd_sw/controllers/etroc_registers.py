"""
Authors: Naomi Gonzalez and Hayden Swanson

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
~~~~~~~~~~~DO NOT CHANGE FILE~~~~~~~~~~~~~
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 

Description:
This file defines ETROC2 register addresses and formats (e.g bit length, mask, offset)
- ETROC registers are places into Pixel or Peripheral Registers
- Code handles the logic of registers that are split across two addresses
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

def validate_is_pixel(row: int = None, col: int = None) -> bool:
    """
    Checks if it is a pixel.
    """
    if row is None and col is None:
        is_pixel = False
    elif row is not None and col is not None:
        is_pixel = True
    else:
        # Exactly one supplied
        raise ValueError("row and col must both be provided together (or both omitted)")
    
    if is_pixel:
        if not row in range(16) or not col in range(16):
            raise ValueError(f"Row and Col should be between 0..15, you gave: {row=}, {col=}")
    return is_pixel

@dataclass(frozen=True)
class RegChunk:
    """
    Select part of a real physical ETROC2 physical register
    """
    adr: int
    bit_mask: int
    is_status_reg: bool = False

    @property
    def offset(self) -> int:
        """
        Calculates the number of 0 bits in the bit_mask word until you get a 1

        For example the bit mask, 0b1111_1100 has an offset of 2 (start counting at 0 from the right)
        """
        if self.bit_mask == 0:
            raise ValueError("mask=0")
        return (self.bit_mask & -self.bit_mask).bit_length() - 1   # index of lowest set bit

    @property
    def length(self) -> int:
        """
        Total length of the group of 1's in the bit_mask

        For example, 0b1100_0000 has a length of 2.
        """
        off = self.offset
        shifted = self.bit_mask >> off
        # Verify contiguity: shifted should be like 0b111... with no internal 0
        if shifted & (shifted + 1):
            raise ValueError(f"mask 0x{self.bit_mask:X} not contiguous")
        return shifted.bit_length()
    
    def calc_full_address(self, row: int = None, col: int = None, broadcast: bool = False) -> int:
        ## Check if it is for pixel
        is_pixel = validate_is_pixel(row=row, col=col)
        # # # # PIXEL ADDRESS # # # # 
        if is_pixel:
            return self.adr \
                    | row << 5 \
                    | col << 9 \
                    | broadcast << 13 \
                    | self.is_status_reg <<14 \
                    | is_pixel << 15
        
        # # # # PERIPHERY ADDRESS # # # #
        # Construct a full ETROC periphery register address based on table 11 in ETROC2 Manual.
        if self.is_status_reg:
            return self.adr | 0x100
        return self.adr

class RegMixin:
    """
    Contains useful methods and properties for the custom grouping of address 
    that make up one register definition (based on ETROC2 Manual)
    """
    
    @property
    def RegChunks(self) -> Tuple[RegChunk, ...]:
        """
        Defines a better name for the confusing name "value" given by defualt by enum
        """
        return self.value

    @property
    def total_bits(self) -> int:
        """Adds up the lengths of the chunks"""
        return sum(c.length for c in self.RegChunks)
    
    @property
    def local_addresses(self) -> list[int]:
        return [r.adr for r in self.RegChunks]
    
    def full_addresses(self, row:int = None, col:int = None, broadcast:bool = False) -> list[int]:
        return [
            r.calc_full_address(row=row, col=col, broadcast=broadcast) for r in self.RegChunks]
    
    @property
    def is_status_reg(self) -> bool:
        """Returns True if all registers are status registers for each register chunk"""
        return all(reg.is_status_reg for reg in self.RegChunks)
    
    def split_value(self, value) -> list[int]:
        """
        Split the incoming value to be written based on the bitmasks

        IMPORTANT: This assumes that the first register in register chunk corresponds to the first bits
        """
        split_values = []
        remaining = value
        for reg_chunk in self.RegChunks:
            n = reg_chunk.length
            low_bits = remaining & ((1 << n) - 1)
            remaining >>= n # consume
            masked_value = low_bits << reg_chunk.offset
            split_values.append(masked_value)
        return split_values
    
    def merge_values(self, values: list) -> int:
        """
        Inverse of split_value: take per-address masked values (ensure it is the same order as defined in the Enum) 
        and reconstruct the composite integer
        """
        if not isinstance(values, list):
            values = [values]
        if len(values) != len(self.RegChunks):
            raise ValueError("length mismatch")
            
        composite = 0
        shift = 0
        for val, chunk in zip(values, self.RegChunks):
            raw = (val & chunk.bit_mask) >> chunk.offset
            composite |= raw << shift
            shift += chunk.length
        return composite
    

######### PIXEL REG DEFINITIONS ############

class PixReg(RegMixin, Enum):
    """
    Information extracted from table 13 in ETROC2 documentaition (page 57)
    https://indico.cern.ch/event/1288660/contributions/5415154/attachments/2651263/4590830/ETROC2_Reference_Manual%200.41.pdf
    """
    L1Adelay        = [RegChunk(adr = 8,  bit_mask = 0b1000_0000), RegChunk(adr = 9, bit_mask = 0b1111_1111)]
    CLKEn_THCal     = [RegChunk(adr = 3,  bit_mask = 0b0000_1000)]
    Bypass_THCal    = [RegChunk(adr = 3,  bit_mask = 0b0000_0100)]
    BufEn_THCal     = [RegChunk(adr = 3,  bit_mask = 0b0000_0010)]
    RSTn_THCal      = [RegChunk(adr = 3,  bit_mask = 0b0000_0001)]
    ScanStart_THCal = [RegChunk(adr = 3,  bit_mask = 0b0001_0000)]
    DAC             = [RegChunk(adr = 4,  bit_mask = 0b1111_1111), RegChunk(adr = 5, bit_mask = 0b0000_0011)]
    TH_offset       = [RegChunk(adr = 5,  bit_mask = 0b1111_1100)]
    enable_TDC      = [RegChunk(adr = 6,  bit_mask = 0b1000_0000)]
    disTrigPath     = [RegChunk(adr = 7,  bit_mask = 0b0000_0100)]
    disDataReadout  = [RegChunk(adr = 7,  bit_mask = 0b0000_0010)]
    QInjEn          = [RegChunk(adr = 1,  bit_mask = 0b0010_0000)]
    lowerCal        = [RegChunk(adr = 10, bit_mask = 0b1111_1111), RegChunk(adr = 11, bit_mask = 0b0000_0011)]
    upperCal        = [RegChunk(adr = 11, bit_mask = 0b1111_1100), RegChunk(adr = 12, bit_mask = 0b0000_1111)]
    upperTOA        = [RegChunk(adr = 13, bit_mask = 0b1000_0000), RegChunk(adr = 14, bit_mask = 0b1111_1111)]
    lowerTOA        = [RegChunk(adr = 12, bit_mask = 0b1111_0000), RegChunk(adr = 13, bit_mask = 0b0011_1111)]
    lowerTOT        = [RegChunk(adr = 15, bit_mask = 0b1111_1111), RegChunk(adr = 16, bit_mask = 0b0000_0001)]
    upperTOT        = [RegChunk(adr = 16, bit_mask = 0b1111_1110), RegChunk(adr = 17, bit_mask = 0b0000_0011)]
    lowerCalTrig    = [RegChunk(adr = 17, bit_mask = 0b1111_1100), RegChunk(adr = 18, bit_mask = 0b0000_1111)]
    upperCalTrig    = [RegChunk(adr = 18, bit_mask = 0b1111_0000), RegChunk(adr = 19, bit_mask = 0b0011_1111)]
    lowerTOATrig    = [RegChunk(adr = 19, bit_mask = 0b1100_0000), RegChunk(adr = 20, bit_mask = 0b1111_1111)]
    upperTOATrig    = [RegChunk(adr = 21, bit_mask = 0b1111_1111), RegChunk(adr = 22, bit_mask = 0b0000_0011)]
    lowerTOTTrig    = [RegChunk(adr = 22, bit_mask = 0b1111_1100), RegChunk(adr = 23, bit_mask = 0b0000_0111)]
    upperTOTTrig    = [RegChunk(adr = 23, bit_mask = 0b1111_1000), RegChunk(adr = 24, bit_mask = 0b0000_1111)]
    
    # STATUS REGISTERS
    ACC          = [RegChunk(adr = 5, bit_mask = 0b1111_1111, is_status_reg = True),
                    RegChunk(adr = 6, bit_mask = 0b1111_1111, is_status_reg = True)]
    
    ScanDone     = [RegChunk(adr = 1, bit_mask = 0b0000_0001, is_status_reg = True)]
    
    BL           = [RegChunk(adr = 2, bit_mask = 0b1111_1111, is_status_reg = True), 
                    RegChunk(adr = 3, bit_mask = 0b0000_0011, is_status_reg = True)]
    
    NW           = [RegChunk(adr = 1, bit_mask = 0b0001_1110, is_status_reg = True)]

    TH           = [RegChunk(adr = 3, bit_mask = 0b1100_0000, is_status_reg = True), 
                    RegChunk(adr = 4, bit_mask = 0b1111_1111, is_status_reg = True)]
    
    THState      = [RegChunk(adr = 1, bit_mask = 0b1110_0000, is_status_reg = True)]


class PeriReg(RegMixin, Enum):
    """
    Registers in the Periphery of the ETROC, not in pixel registers.

    Information extracted from table 15 in ETROC2 documentaition (page 61)
    https://indico.cern.ch/event/1288660/contributions/5415154/attachments/2651263/4590830/ETROC2_Reference_Manual%200.41.pdf
    """
    VRefGen_PD            = [RegChunk(adr = 3,  bit_mask = 0b1000_0000)]
    PLL_ENABLEPLL         = [RegChunk(adr = 3,  bit_mask = 0b0100_0000)]
    PLL_vcoRailMode       = [RegChunk(adr = 3,  bit_mask = 0b0010_0000)]
    PLL_vcoDAC            = [RegChunk(adr = 3,  bit_mask = 0b0000_1111)]
    asyResetGlobalReadout = [RegChunk(adr = 14, bit_mask = 0b1000_0000)]
    asyResetFastcommand   = [RegChunk(adr = 14, bit_mask = 0b0100_0000)]
    asyResetChargeInj     = [RegChunk(adr = 14, bit_mask = 0b0010_0000)]
    readoutClockWidthPixel= [RegChunk(adr = 14, bit_mask = 0b0000_1111)]
    RTx_AmplSel           = [RegChunk(adr = 17, bit_mask = 0b1110_0000)]
    chargeInjectionDelay  = [RegChunk(adr = 17, bit_mask = 0b0001_1111)]
    disLTx                = [RegChunk(adr = 18, bit_mask = 0b1000_0000)]
    onChipL1AConf         = [RegChunk(adr = 18, bit_mask = 0b0110_0000)]
    fcDataDelayEn         = [RegChunk(adr = 18, bit_mask = 0b0001_0000)]
    fcClkDelayEn          = [RegChunk(adr = 18, bit_mask = 0b0000_1000)]
    fcSelfAlignEn         = [RegChunk(adr = 18, bit_mask = 0b0000_0100)]
    softBoot              = [RegChunk(adr = 18, bit_mask = 0b0000_0010)]
    disPowerSequence      = [RegChunk(adr = 18, bit_mask = 0b0000_0001)]
    disRTx                = [RegChunk(adr = 19, bit_mask = 0b1000_0000)]
    singlePort            = [RegChunk(adr = 19, bit_mask = 0b0100_0000)]
    serRateRight          = [RegChunk(adr = 19, bit_mask = 0b0011_0000)]
    serRateLeft           = [RegChunk(adr = 19, bit_mask = 0b0000_1100)]
    linkResetTestPattern  = [RegChunk(adr = 19, bit_mask = 0b0000_0010)]
    disScrambler          = [RegChunk(adr = 19, bit_mask = 0b0000_0001)]
    eFuse_TCKHP           = [RegChunk(adr = 20, bit_mask = 0b1111_0000)]
    triggerGranularity    = [RegChunk(adr = 20, bit_mask = 0b0000_1110)]
    mergeTriggerData      = [RegChunk(adr = 20, bit_mask = 0b0000_0001)]
    eFuse_Prog            = [
        RegChunk(adr = 22, bit_mask = 0b1111_1111),
        RegChunk(adr = 23, bit_mask = 0b1111_1111),
        RegChunk(adr = 24, bit_mask = 0b1111_1111),
        RegChunk(adr = 25, bit_mask = 0b1111_1111),
    ]


# --------------------------------------------------------------
# Testing Script (Optional)
# --------------------------------------------------------------
if __name__ == "__main__":
    def check(reg, value, expected):
        got = reg.split_value(value)
        assert got == expected, f"{reg.name} value {bin(value)} expected {list(map(bin, expected))} got {list(map(bin, got))}"

    # ---- PixReg.L1Adelay ---- #
    check(PixReg.L1Adelay, 0b0,            [0b0000_0000, 0b0000_0000])
    check(PixReg.L1Adelay, 0b1,            [0b1000_0000, 0b0000_0000])
    check(PixReg.L1Adelay, 0b10,           [0b0000_0000, 0b0000_0001])
    check(PixReg.L1Adelay, 0b11,           [0b1000_0000, 0b0000_0001])
    check(PixReg.L1Adelay, 0b1_0000_0000,  [0b0000_0000, 0b1000_0000])   
    check(PixReg.L1Adelay, 0b1_1111_1111,  [0b1000_0000, 0b1111_1111])  
    check(PixReg.L1Adelay, 0b10_1010_1010, [0b0000_0000, 0b0101_0101])
    print("L1A Delay Reg passed")

    # ---- Single-bit single-chunk register: CLKEn_THCal (mask 0b0000_1000, offset 3, length 1) ---- #
    check(PixReg.CLKEn_THCal, 0b0,  [0b0000_0000])
    check(PixReg.CLKEn_THCal, 0b1,  [0b0000_1000])
    check(PixReg.CLKEn_THCal, 0b10, [0b0000_0000])
    check(PixReg.CLKEn_THCal, 0b11, [0b0000_1000])
    print("CLKEn_THCal Reg passed")

    # ---- Multi-bit single-chunk register: TH_offset (mask 0b1111_1100, offset 2, length 6) ---- #
    check(PixReg.TH_offset, 0b000000,        [0b0000_0000])
    check(PixReg.TH_offset, 0b000001,        [0b0000_0100])
    check(PixReg.TH_offset, 0b000010,        [0b0000_1000])
    check(PixReg.TH_offset, 0b000011,        [0b0000_1100])
    check(PixReg.TH_offset, 0b111111,        [0b1111_1100])  
    check(PixReg.TH_offset, 0b1_1111_1111,   [0b1111_1100])
    print("Single-chunk register tests passed")



    print(PixReg[PixReg.BufEn_THCal])