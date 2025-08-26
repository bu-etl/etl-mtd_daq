"""
Authors: Naomi Gonzalez and Hayden Swanson

Description:
Reads from mux64 which is a chip on ETL Readout Board
that handles monitoring of temperatures and voltages on the ETROCs and Readout Board
"""
from .lpgbt_controller import lpgbt_chip
from ..utils.Configure_from_DB import etl_asic_config_from_db
from typing import Union
from dataclasses import dataclass
try:
    from tabulate import tabulate
    has_tabulate = True
except ModuleNotFoundError:
    print ("Package `tabulate` not found.")
    has_tabulate = False

VERBOSE_OUTPUT = False 


class Mux64Error(Exception):
    pass

@dataclass
class Channel:
    """
    adc_port: the physical pin on the MUX64 that is connected to a monitored voltage (0-63)
    name: name of the connection based on configuration
    R1: Resistor used in converting raw adc
    R2: Resistor used in convereting raw adc
    """
    name: str
    adc_port: int
    R1: float
    R2: float
    comment: str | None

    @classmethod
    def from_dict(cls, config: dict):
        return cls(
            name     = config["register"],
            adc_port = config["adc_port"],
            R1       = config["R1"],
            R2       = config["R2"],
            comment  = config["comment"]
        )
    
class mux64_chip:
    """
    mux_out: Current selected output channel of mux64
    R01: Resistor between MUX output and lpGBT input
    R02: Resistor between lpGBT input and ground

    #TODO: Change to lpgbt controller
    gain: 
    offset: Offset from neg refrence point when reading adc  
    """
    R01: float
    R02: float
    mux_out: Channel

    def __init__(self, lpgbt: lpgbt_chip, board='rbv3'): 
        """
        Calls DB to get mapping of all signals connected to mux64
        """
        self.lpgbt = lpgbt
        self.config = etl_asic_config_from_db('MUX64')
        self.config = self.config["MUX64"]
        self.channel_map: dict[int, Channel] = {
            config['adc_port']: Channel.from_dict(config) for config in self.config["configurations"]["ADC"]}
        self.selected_channel = None
        self.mux_out = None
        
        #TODO: Change this to lpgbt controller
        self.cal_gain = None
        self.cal_offset = None
        self.calibrated = False


        #TODO: get R01 and R02 from DB (This is for RBF3 and above)
        self.R01 = 20
        self.R02 = 20


    def find_channel(self, identifier: Union[int, str]) -> Channel:
        """
        Finds mux64 channel in dictionary based on name or number
        """
        if isinstance(identifier, int):
            if identifier not in self.channel_map:
                raise Mux64Error(f"Channel with adc_port {identifier} not found")
            return self.channel_map[identifier]
        elif isinstance(identifier, str):
            for channel in self.channel_map.values():
                if channel.name == identifier:
                    return channel
            raise Mux64Error(f"Channel with name {identifier} not found")
        else:
            raise Mux64Error("Identifier must be an int (adc_port) or str (name)")


    def select_channel(self, channel: Channel):
        """
        Writes to mux64 select pins to select ouput of mux64
        """    
        if not isinstance(channel, Channel):
            raise NotImplementedError(f"Channel is not a Channel type, instead you gave {type(channel)}")
        self.selected_channel = channel

        for i in range(6):
            s = (channel.adc_port >> i) & 0x1
            self.lpgbt.write_gpio_output(f"MUXCNT{i+1}", s)

        self.mux_out = channel


    def read_channel(self, channel_identifier: Union[int, str], calib = True) -> float:
        """
        Physicaly selects channel and then reads mux64 output voltage 
        """
        channel = self.find_channel(channel_identifier)
        self.select_channel(channel)


        raw_adc = self.lpgbt.read_adc("MUX64OUT")
        # ------------
        #TODO: Discuss moving this to lpgbt controller when reading lpGBT ADC
        raw_adc_calib = raw_adc*self.cal_gain/1.85 + (512 - self.cal_offset)
        # ------------

        value = raw_adc_calib if calib else raw_adc
        voltage_direct = value / (2**10 - 1)

        #TODO: Use a conversion factor funciton that utalizes r01 and r02 to calculate this value (This is for RBF3 and above)
        voltage = voltage_direct * ((channel.R1 + channel.R2) / channel.R2)

        return raw_adc, raw_adc_calib, voltage_direct, voltage


    def read_all_ch(self):
        """
        Read and prints all signals connected to mux64
        """
        table = []
        for i in range(64):
            try:
                raw, calib, volt_dit, volt = self.read_channel(i)
                current = self.mux_out
                if VERBOSE_OUTPUT:
                    table.append([current.name, current.adc_port, raw, calib, volt_dit, volt, current.comment])
                else:
                    table.append([current.name, current.adc_port, volt, current.comment])
            except Mux64Error as error: 
                ...

        if VERBOSE_OUTPUT:
            headers = ["Channel","Pin", "Reading (raw)", "Reading (calib)", "Voltage (direct)", "Voltage (conv)", "Comment"]
            data_string = "{:<20}{:<20}{:<20.0f}{:<20.0f}{:<20.3f}{:<20.3f}{:<20}"
        else:
            headers = ["Channel","Pin", "Voltage", "Comment"]
            data_string = "{:<20}{:<20}{:<20.3f}{:<20}"

        if has_tabulate:
            print(tabulate(table, headers=headers,  tablefmt="simple_outline"))
        else:
            header_string = "{:<20}"*len(headers)
            print(header_string.format(*headers))
            for line in table:
                print(data_string.format(*line))


    # ------------------------------------------------------------------------------
    # TODO: NEED TO DISCUSS MOVING THIS TO LPGBT CONTROLLER
    # ------------------------------------------------------------------------------
    def calibrate_adc(self):
        '''
        Calculates the offset and gain of the lpGBT ADCs
        '''
        LPGBT = self.lpgbt
        offset = LPGBT.read_adc(0xf)

        intial_val = LPGBT.read_reg(LPGBT.Reg['ADCMON'])
        mask = ~(1 << 4)
        LPGBT.write_reg(LPGBT.Reg['ADCMON'], intial_val & mask)

        # ADC = (Vdiff/Vref)*Gain*512 + Offset
        gain = 2*abs(LPGBT.read_adc(0xC)-offset)/512
        print(f"Calibrated lpgbt  ADC. Gain: {gain} / Offset: {offset}")

        LPGBT.write_reg(LPGBT.Reg['ADCMON'], intial_val)
        if gain < 1.65 or gain > 2 or offset < 490 or offset > 530:
            raise RuntimeError("ADC Calibration Failed!")

        self.cal_gain = gain
        self.cal_offset = offset
        self.calibrated = True


    # ------------------------------------------------------------------------------
    # TEMPORARY FUNCTION TILL WE FIX DB FORMAT
    # ------------------------------------------------------------------------------
    def write_config(self):
        """
        Writes to all lpGBT registers default Tamalero configuration value based on csv file
        """
        import csv
        with open('tamalero_lpgbt_config.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # skip the header row
            for register, value in reader:
                if value == 'N/A' or "POWERUP" in register.upper():
                    print(register)
                    continue
                self.lpgbt.write_reg(
                    self.lpgbt.Reg[register], int(value,16))


