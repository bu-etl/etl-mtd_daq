"""
Authors: Naomi Gonzalez and Hayden Swanson

Outline script of ETROC registers
"""
def field_offset(mask: int) -> int:
    if mask == 0:
        raise ValueError("mask=0")
    return (mask & -mask).bit_length() - 1   # index of lowest set bit

def field_length(mask: int) -> int:
    off = field_offset(mask)
    shifted = mask >> off
    # Verify contiguity: shifted should be like 0b111... with no internal 0
    if shifted & (shifted + 1):
        raise ValueError(f"mask 0x{mask:X} not contiguous")
    return shifted.bit_length()

PixConfig = {
    "L1Adelay": [
        {"address": 8, "bit_mask": 0b1000_0000},
        {"address": 9, "bit_mask": 0b1111_1111}
    ],
    "disTrigPath": {"address": 7, "bit_mask": 0b0000_0100},
    "QInjEn": {"address": 1, "bit_mask": 0b0010_0000},
    "lowerCal": [
        {"address": 10, "bit_mask": 0b1111_1111},
        {"address": 11, "bit_mask": 0b0000_0011}   
    ],
    "upperCal": [
        {"address": 11, "bit_mask": 0b1111_1100},
        {"address": 12, "bit_mask": 0b0000_1111}   
    ],
    "upperTOA": [
        {"address": 13, "bit_mask": 0b1000_0000},
        {"address": 14, "bit_mask": 0b1111_1111}
    ],
    "lowerTOA": [
        {"address": 12, "bit_mask": 0b1111_0000},
        {"address": 13, "bit_mask": 0b0011_1111}
    ],
    "lowerTOT": [
        {"address": 15, "bit_mask": 0b1111_1111},
        {"address": 16, "bit_mask": 0b0000_0001}
    ],
    "upperTOT": [
        {"address": 16, "bit_mask": 0b1111_1110},
        {"address": 17, "bit_mask": 0b0000_0011}
    ],
    "lowerCalTrig": [
        {"address": 17, "bit_mask": 0b1111_1100},
        {"address": 18, "bit_mask": 0b0000_1111}
    ], 
    "upperCalTrig": [
        {"address": 18, "bit_mask": 0b1111_0000},
        {"address": 19, "bit_mask": 0b0011_1111}
    ],
    "lowerTOATrig": [
        {"address": 19, "bit_mask": 0b1100_0000},
        {"address": 20, "bit_mask": 0b1111_1111}
    ],
    "upperTOATrig": [
        {"address": 21, "bit_mask": 0b1111_1111},
        {"address": 22, "bit_mask": 0b0000_0011}
    ],
    "lowerTOTTrig": [
        {"address": 22, "bit_mask": 0b1111_1100},
        {"address": 23, "bit_mask": 0b0000_0111}
    ],
    "upperTOTTrig": [
        {"address": 23, "bit_mask": 0b1111_1000},
        {"address": 24, "bit_mask": 0b0000_1111}
    ],
}

######### PERIPHERY REG DEFINITIONS ############
PeripheryConfig = {
    "VRefGen_PD": {"address": 3, "bit_mask": 0b1000_0000, "offset": 7, "length": 1},
    "PLL_ENABLEPLL": {"address": 3, "bit_mask": 0b0100_0000, "offset": 5, "length": 1},
    "PLL_vcoRailMode": {"address": 3, "bit_mask": 0b0010_0000, "offset":4, "length": 1},
    "PLL_vcoDAC": {"address": 3, "bit_mask": 0b0000_1111, "offset": 0, "length": 4},
    "asyResetGlobalReadout": {"address": 14, "bit_mask": 0b1000_0000},
    "asyResetFastcommand": {"address": 14, "bit_mask": 0b0100_0000},
    "asyResetChargeInj": {"address": 14, "bit_mask": 0b0010_0000},
    "readoutClockWidthPixel": {"address": 14, "bit_mask": 0b0000_1111},
    "RTx_AmplSel": {"address": 17, "bit_mask": 0b1110_0000},
    "chargeInjectionDelay": {"address": 17, "bit_mask": 0b0001_1111},
    "disLTx": {"address": 18, "bit_mask": 0b1000_0000},
    "onChipL1AConf": {"address": 18, "bit_mask": 0b0110_0000},
    "fcDataDelayEn": {"address": 18, "bit_mask": 0b0001_0000},
    "fcClkDelayEn": {"address": 18, "bit_mask": 0b0000_1000},
    "fcSelfAlignEn": {"address": 18, "bit_mask": 0b0000_0100},
    "softBoot": {"address": 18, "bit_mask": 0b0000_0010},
    "disPowerSequence": {"address": 18, "bit_mask": 0b0000_0001},
    "disRTx": {"address": 19, "bit_mask": 0b1000_0000},
    "singlePort": {"address": 19, "bit_mask": 0b0100_0000},
    "serRateRight": {"address": 19, "bit_mask": 0b0011_0000},
    "serRateLeft": {"address": 19, "bit_mask": 0b0000_1100},
    "linkResetTestPattern": {"address": 19, "bit_mask": 0b0000_0010},
    "disScrambler": {"address": 19, "bit_mask": 0b0000_0001},
    "eFuse_TCKHP": {"address": 20, "bit_mask": 0b1111_0000},
    "triggerGranularity": {"address": 20, "bit_mask": 0b0000_1110},
    "readoutClockWidthPixel": {"address": 20, "bit_mask": 0b0000_0001},
    "eFuse_Prog": [
        {"address": 22, "bit_mask": 0b1111_1111},
        {"address": 23, "bit_mask": 0b1111_1111},
        {"address": 24, "bit_mask": 0b1111_1111},
        {"address": 25, "bit_mask": 0b1111_1111},
    ]
}
#############################

for adr, value in reg_split(PixelReg["L1Adelay"], value):
    write(adr, value)