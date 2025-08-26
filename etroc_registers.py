"""
Authors: Naomi Gonzalez and Hayden Swanson

Outline script of ETROC registers
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

@dataclass(frozen=True)
class RegChunk:
    adr: int
    bit_mask: int
    is_status_reg: bool = False

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

class RegMixin:
    """Mixin for Enums"""
    
    @property
    def RegChunks(self) -> Tuple[RegChunk, ...]:
        return self.value

    @property
    def total_bits(self) -> int:
        return sum(c.length for c in self.RegChunks)
    
    @property
    def addresses(self) -> list[int]:
        return sorted(set(c.adr for c in self.RegChunks))
    
    @property
    def is_status_reg(self):
        return all(reg.is_status_reg for reg in self.RegChunks)
    
    def split_value(self, value) -> list[int]:
        """
        Splits value into chunks based on bit_masks and ordering of the register chunks (RegChunk)

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
        Inverse of split_value: take per-address masked values (same order
        as self.RegChunks) and reconstruct the composite integer (LSB-first).
        """
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

    Note the registers are not actual registers in the ETROC. 
    The register names are not very useful, so we grouped the names that are spread across registers as the registers we manipulate in software.
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

    Note the registers are not actual registers in the ETROC. 
    The register names are not very useful, so we grouped the names that are spread across registers as the registers we manipulate in software.
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
    eFuse_Prog            = [
        RegChunk(adr = 22, bit_mask = 0b1111_1111),
        RegChunk(adr = 23, bit_mask = 0b1111_1111),
        RegChunk(adr = 24, bit_mask = 0b1111_1111),
        RegChunk(adr = 25, bit_mask = 0b1111_1111),
    ]





#### TESTING
# l1a_reg = PixReg["L1Adelay"]
# print(l1a_reg.total_bits, l1a_reg.addresses)

# val = 0b1001_1000_1

# print("GOAL", 0b1000_0000, 0b1001_1000)
# values = l1a_reg.split_value(val)
# for v in values:
#     print(v, bin(v), hex(v))


# for reg in l1a_reg.RegChunks:
#     print(reg.adr, reg.address_name, reg.length, reg.offset, reg.bit_mask)


# print(type(PeriReg.disScrambler))

# print(isinstance(PeriReg.disLTx, PeriReg))