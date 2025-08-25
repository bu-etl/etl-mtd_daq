"""
Authors: Naomi Gonzalez and Hayden Swanson

Outline script of ETROC registers
"""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Tuple, List

@dataclass(frozen=True)
class RegChunk:
    adr: int
    bit_mask: int

    @property
    def offset(self) -> int:
        if self.bit_mask == 0:
            raise ValueError("mask=0")
        return (self.bit_mask & -self.bit_mask).bit_length() - 1   # index of lowest set bit

    @property
    def length(self) -> int:
        off = self.offset
        shifted = self.bit_mask >> off
        # Verify contiguity: shifted should be like 0b111... with no internal 0
        if shifted & (shifted + 1):
            raise ValueError(f"mask 0x{self.bit_mask:X} not contiguous")
        return shifted.bit_length()
    
    @property
    def address_name(self) -> str:
        return PixRegAddr(self.adr).name

class RegMixin:
    """Mixin for Enums"""
    
    @property
    def RegChunks(self) -> Tuple[RegChunk, ...]:
        return self.value

    @property
    def total_bits(self) -> int:
        return sum(c.length for c in self.RegChunks)
    
    def iter_write(self, value) -> List[Tuple[int, int]]:
        ...

    def iter_read(self) -> List[int]:
        ...

######### PIXEL REG DEFINITIONS ############
class PixRegAddr(IntEnum):
    PixRnCnCfg0= 0
    PixRnCnCfg1= 1
    PixRnCnCfg2= 2
    PixRnCnCfg3= 3
    PixRnCnCfg4= 4
    PixRnCnCfg5= 5
    PixRnCnCfg6= 6
    PixRnCnCfg7= 7
    PixRnCnCfg8= 8
    PixRnCnCfg9= 9
    PixRnCnCfg10 = 10
    PixRnCnCfg11 = 11
    PixRnCnCfg12 = 12
    PixRnCnCfg13 = 13
    PixRnCnCfg14 = 14
    PixRnCnCfg15 = 15
    PixRnCnCfg16 = 16
    PixRnCnCfg17 = 17
    PixRnCnCfg18 = 18
    PixRnCnCfg19 = 19
    PixRnCnCfg20 = 20
    PixRnCnCfg21 = 21
    PixRnCnCfg22 = 22
    PixRnCnCfg23 = 23
    PixRnCnCfg24 = 24

class PixelReg(Enum, RegMixin):
    """
    Information extracted from table 13 in ETROC2 documentaition (page 57)
    https://indico.cern.ch/event/1288660/contributions/5415154/attachments/2651263/4590830/ETROC2_Reference_Manual%200.41.pdf

    Note the registers are not actual registers in the ETROC. 
    The register names are not very useful, so we grouped the names that are spread across registers as the registers we manipulate in software.
    """
    L1Adelay     = [RegChunk(adr = 8,  bit_mask = 0b1000_0000), RegChunk(adr = 9, bit_mask = 0b1111_1111)]
    disTrigPath  = [RegChunk(adr = 7,  bit_mask = 0b0000_0100)]
    QInjEn       = [RegChunk(adr = 1,  bit_mask = 0b0010_0000)]
    lowerCal     = [RegChunk(adr = 10, bit_mask = 0b1111_1111), RegChunk(adr = 11, bit_mask = 0b0000_0011)]
    upperCal     = [RegChunk(adr = 11, bit_mask = 0b1111_1100), RegChunk(adr = 12, bit_mask = 0b0000_1111)]
    upperTOA     = [RegChunk(adr = 13, bit_mask = 0b1000_0000), RegChunk(adr = 14, bit_mask = 0b1111_1111)]
    lowerTOA     = [RegChunk(adr = 12, bit_mask = 0b1111_0000), RegChunk(adr = 13, bit_mask = 0b0011_1111)]
    lowerTOT     = [RegChunk(adr = 15, bit_mask = 0b1111_1111), RegChunk(adr = 16, bit_mask = 0b0000_0001)]
    upperTOT     = [RegChunk(adr = 16, bit_mask = 0b1111_1110), RegChunk(adr = 17, bit_mask = 0b0000_0011)]
    lowerCalTrig = [RegChunk(adr = 17, bit_mask = 0b1111_1100), RegChunk(adr = 18, bit_mask = 0b0000_1111)]
    upperCalTrig = [RegChunk(adr = 18, bit_mask = 0b1111_0000), RegChunk(adr = 19, bit_mask = 0b0011_1111)]
    lowerTOATrig = [RegChunk(adr = 19, bit_mask = 0b1100_0000), RegChunk(adr = 20, bit_mask = 0b1111_1111)]
    upperTOATrig = [RegChunk(adr = 21, bit_mask = 0b1111_1111), RegChunk(adr = 22, bit_mask = 0b0000_0011)]
    lowerTOTTrig = [RegChunk(adr = 22, bit_mask = 0b1111_1100), RegChunk(adr = 23, bit_mask = 0b0000_0111)]
    upperTOTTrig = [RegChunk(adr = 23, bit_mask = 0b1111_1000), RegChunk(adr = 24, bit_mask = 0b0000_1111)]

    @property
    def RegChunks(self) -> Tuple[RegChunk, ...]:
        return self.value
    @property
    def total_bits(self) -> int:
        return sum(s.length for s in self.RegChunks)

######### PERIPHERY REG DEFINITIONS ############
class PeripheryRegAddr(IntEnum):
    PeriCfg0 = 0
    PeriCfg1 = 1
    PeriCfg2 = 2
    PeriCfg3 = 3
    PeriCfg4 = 4
    PeriCfg5 = 5
    PeriCfg6 = 6
    PeriCfg7 = 7
    PeriCfg8 = 8
    PeriCfg9 = 9
    PeriCfg10 = 10
    PeriCfg11 = 11
    PeriCfg12 = 12
    PeriCfg13 = 13
    PeriCfg14 = 14
    PeriCfg15 = 15
    PeriCfg16 = 16
    PeriCfg17 = 17
    PeriCfg18 = 18
    PeriCfg19 = 19
    PeriCfg20 = 20
    PeriCfg21 = 21
    PeriCfg22 = 22
    PeriCfg23 = 23
    PeriCfg24 = 24
    PeriCfg25 = 25
    PeriCfg26 = 26
    PeriCfg27 = 27
    PeriCfg28 = 28
    PeriCfg29 = 29
    PeriCfg30 = 30
    PeriCfg31 = 31

class PeripheryReg(Enum, RegMixin):
    """
    Registers in the Periphery of the ETROC, not in pixel registers.

    Information extracted from table 15 in ETROC2 documentaition (page 61)
    https://indico.cern.ch/event/1288660/contributions/5415154/attachments/2651263/4590830/ETROC2_Reference_Manual%200.41.pdf

    Note the registers are not actual registers in the ETROC. 
    The register names are not very useful, so we grouped the names that are spread across registers as the registers we manipulate in software.
    """
    VRefGen_PD            = [RegChunk(3,  0b1000_0000)]
    PLL_ENABLEPLL         = [RegChunk(3,  0b0100_0000)]
    PLL_vcoRailMode       = [RegChunk(3,  0b0010_0000)]
    PLL_vcoDAC            = [RegChunk(3,  0b0000_1111)]
    asyResetGlobalReadout = [RegChunk(14, 0b1000_0000)]
    asyResetFastcommand   = [RegChunk(14, 0b0100_0000)]
    asyResetChargeInj     = [RegChunk(14, 0b0010_0000)]
    readoutClockWidthPixel= [RegChunk(14, 0b0000_1111)]
    RTx_AmplSel           = [RegChunk(17, 0b1110_0000)]
    chargeInjectionDelay  = [RegChunk(17, 0b0001_1111)]
    disLTx                = [RegChunk(18, 0b1000_0000)]
    onChipL1AConf         = [RegChunk(18, 0b0110_0000)]
    fcDataDelayEn         = [RegChunk(18, 0b0001_0000)]
    fcClkDelayEn          = [RegChunk(18, 0b0000_1000)]
    fcSelfAlignEn         = [RegChunk(18, 0b0000_0100)]
    softBoot              = [RegChunk(18, 0b0000_0010)]
    disPowerSequence      = [RegChunk(18, 0b0000_0001)]
    disRTx                = [RegChunk(19, 0b1000_0000)]
    singlePort            = [RegChunk(19, 0b0100_0000)]
    serRateRight          = [RegChunk(19, 0b0011_0000)]
    serRateLeft           = [RegChunk(19, 0b0000_1100)]
    linkResetTestPattern  = [RegChunk(19, 0b0000_0010)]
    disScrambler          = [RegChunk(19, 0b0000_0001)]
    eFuse_TCKHP           = [RegChunk(20, 0b1111_0000)]
    triggerGranularity    = [RegChunk(20, 0b0000_1110)]
    readoutClockWidthPixel_bit0 = [RegChunk(20, 0b0000_0001)]  # was duplicate key in original dict
    eFuse_Prog            = [
        RegChunk(22, 0b1111_1111),
        RegChunk(23, 0b1111_1111),
        RegChunk(24, 0b1111_1111),
        RegChunk(25, 0b1111_1111),
    ]