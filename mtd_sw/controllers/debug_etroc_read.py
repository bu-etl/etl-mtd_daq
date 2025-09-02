from etroc_registers import PixReg, PeriReg

#### CHECK WRITING IN TH CALIBRATION
def r_test(register, values, read_value, read_addresses, row=None, col=None):
    register = PixReg.get(register) or PeriReg.get(register)
    assert register.full_addresses(row=row,col=col) == read_addresses, f"{register} full addresses dont match: {register.full_addresses(row=row,col=col)}, {read_addresses=}"
    assert register.merge_values(values) == read_value, f"{register} merged value incorrect"

def w_test(register, input_val, read, written_val, written_adr, row=None, col=None):
    register = PixReg.get(register) or PeriReg.get(register)

    if isinstance(read, int):
        read = [read]
    if isinstance(written_val, int):
        written_val = [written_val]
    if isinstance(written_adr, int):
        written_adr = [written_adr]

    for adr, val, bit_mask, r, wr_v, wr_a in zip(register.full_addresses(row=row, col=col), 
                                                 register.split_value(input_val), 
                                                 register.bit_masks, 
                                                 read, 
                                                 written_val, 
                                                 written_adr):
        #   You need to get the current register contents and only change the bits 
        # for that physical ETROC register chunk otherwise you rewrite the entire contents of the register!
        # register_contents = self.i2c_read(reg_address=adr)
        data = (r & ~bit_mask) | val

        assert data == wr_v, f"data does not match for {register}, {data=}, {wr_v=}"
        assert adr  == wr_a, f"adr doent match for {register}, {adr=}, {wr_a=}"
        # self.i2c_write(reg_address=adr, data=data)

###
##### Configuration
###
print(PeriReg.VRefGen_PD.full_addresses())
w_test(
    "VRefGen_PD",
    written_adr=3,
    written_val=152,
    read=24,
    input_val=1,
    row=None, col=None
)


###
##### Calibration of Row=0,Col=0
###
w_test("Bypass_THCal", 
       input_val=0, 
       read=13, 
       written_val=9, 
       written_adr=32771, 
       row=0, col=0)
w_test("BufEn_THCal",
       input_val=1,
       read=9,
       written_val=11,
       written_adr=32771,
       row=0, col=0)
w_test("RSTn_THCal",
       input_val=0,
       read=11,
       written_val=10,
       written_adr=32771,
       row=0, col=0)
w_test("RSTn_THCal",
       input_val=1,
       read=10,
       written_val=11,
       written_adr=32771,
       row=0, col=0)
w_test("ScanStart_THCal",
       input_val=1,
       read=11,
       written_val=27,
       written_adr=32771,
       row=0, col=0)
w_test("ScanStart_THCal",
       input_val=0,
       read=27,
       written_val=11,
       written_adr=32771,
       row=0, col=0)
r_test("ScanDone", 
       values=[160], 
       read_value=0,
       read_addresses=[49153],
       row=0, col=0)
r_test("ScanDone", 
       values=[166], 
       read_value=0,
       read_addresses=[49153],
       row=0, col=0)
r_test("ScanDone", 
       values=[199], 
       read_value=1,
       read_addresses=[49153],
       row=0, col=0)
r_test("NW", 
       values=[199], 
       read_value=3,
       read_addresses=[49153],
       row=0, col=0)
r_test("BL", 
       values=[33, 192], 
       read_value=33,
       read_addresses=[49154, 49155],
       row=0, col=0)

w_test("DAC",
       input_val=36,
       written_val=[36, 40],
       written_adr=[32772, 32773],
       read=[0,40],
       row=0, col=0
)

######

# CHECK CURRENT VALUES
# import yaml
# with open("/home/hayden/Downloads/ETROC2_example.yaml", 'r') as f:
#     data = yaml.load(f, Loader=yaml.Loader)
#     for reg_name, config in data.items():
#         if reg_name in PixReg.__members__:
#             px_reg = PixReg[reg_name]
#             if not px_reg.bit_masks == config["mask"]:
#                 raise Exception(f"Bit masks not the same! For {px_reg}, {px_reg.bit_masks} vs {config["mask"]}")
            
#             if not px_reg.local_addresses == config["address"]:
#                 raise Exception(f"Address not the same! For {px_reg}, {px_reg.local_addresses} vs {config["address"]}")

#         if reg_name in PeriReg.__members__:
#             px_reg = PeriReg[reg_name]
#             if not px_reg.bit_masks == config["mask"]:
#                 raise Exception(f"Bit masks not the same! For {px_reg}, {px_reg.bit_masks} vs {config["mask"]}")
            
#             if not px_reg.local_addresses == config["address"]:
#                 raise Exception(f"Address not the same! For {px_reg}, {px_reg.local_addresses} vs {config["address"]}")
        

# # WRITE THE PYTHON CODE
# import yaml
# with open("/home/hayden/Downloads/ETROC2_example.yaml", 'r') as f:
#     data = yaml.load(f, Loader=yaml.Loader)
#     for reg_name, config in data.items():
#         if reg_name in PeriReg.__members__:
#             px_reg = PeriReg[reg_name]
#             if not px_reg.bit_masks == config["mask"]:
#                 raise Exception(f"Bit masks not the same! For {px_reg}, {px_reg.bit_masks} vs {config["mask"]}")
#             if not px_reg.local_addresses == config["address"]:
#                 raise Exception(f"Address not the same! For {px_reg}, {px_reg.local_addresses} vs {config["address"]}")
#             continue

#         if config["pixel"]:
#             continue
#         if not config["stat"]:
#             continue
        
#         reg_chunks = []
#         for adr, bit_mask in zip(config["address"], config["mask"]):
#             reg_chunks.append(f"RegChunk(adr = {adr}, bit_mask = {bit_mask:#010b}, is_status_reg = True)")

#         print(f"{reg_name} = [{', '.join(reg_chunks)}]")
        