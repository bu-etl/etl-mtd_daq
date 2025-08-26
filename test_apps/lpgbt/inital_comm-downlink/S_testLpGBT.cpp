/*
Author: Naomi Gonzalez

Info: When connecting Frontend Electronics to Serenity, this script tests if we can control a gpio pin 
and run test tamalero setup using SCCIC + IPbus / uHAL
*/

#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <unistd.h>
#include <getopt.h>
#include <string>
#include <iostream>

#include <uhal/ConnectionManager.hpp>
#include <uhal/HwInterface.hpp>
#include "emp/SCCICNode.hpp"
#include "emp/exception.hpp"

// lpgbt regs
#define PIO_DIR_HI    0x053
#define PIO_DIR_LO    0x054
#define OUT_HI        0x055
#define OUT_LO        0x056
#define ULDATASOURCE0 0x128
#define CHIPCONFIG    0x036
#define POWERUP2      0x0fb
#define ROM           0x1d7

void toggleTest(emp::SCCICNode& ic,
                int delay_s,
                int times,
                unsigned addr,
                unsigned gpio)
{
  unsigned dirReg = (gpio < 8) ? PIO_DIR_LO : PIO_DIR_HI;
  unsigned outReg = (gpio < 8) ? OUT_LO     : OUT_HI;
  uint8_t  bit    = 1 << (gpio % 8);

  // set as output
  std::cout << "set as output" << std::endl;
  try{
    ic.icWrite(dirReg, bit, addr);
  } catch (const emp::ICTimeOut&) {
    std::cout << "ERROR: Setting dir - Timeout" << std::endl;
  }
  sleep(1);
  std::cout << "Set as output done" << std::endl;

  uint8_t value = 0;
  for (int i = 0; i < times; ++i) {
    value ^= 1;
    try{
      ic.icWrite(outReg, value, addr);
    } catch (const emp::ICTimeOut&) {
      std::cout << "ERROR: Setting output - Timeout" << std::endl;
    }
    std::cout << "Sleep" << std::endl;
    sleep(delay_s);
  }
  std::cout << "Toggle Test Done" << std::endl;
}

void tamaleroSetUp(emp::SCCICNode& ic,
                   unsigned addr,
                   bool invert)
{

  std::cout << "toggle uplink" << "\n";
  try{ ic.icWrite(ULDATASOURCE0, 0xC0, addr); } 
  catch (const emp::ICTimeOut&) {  }
  usleep(1000);
  try{ ic.icWrite(ULDATASOURCE0, 0x00, addr); }
  catch (const emp::ICTimeOut&) {  }
  std::cout << "toggle uplink done" << "\n";

  if (invert){
    std::cout << "invert" << "\n";
    try { ic.icWrite(CHIPCONFIG, 0x80, addr); }
    catch (const emp::ICTimeOut&) {  }
    std::cout << "invert done" << "\n";
  }

  std::cout << "powerup" << "\n";
  try { ic.icWrite(POWERUP2, 0x06, addr); }
  catch (const emp::ICTimeOut&) {  }
  usleep(1000);
  std::cout << "powerup done" << "\n";

  try { 
    uint8_t romval = ic.icRead(ROM, addr);
    printf("ROM register value: 0x%02X\n", romval);
    return 0;
  }
  catch (const emp::ICTimeOut&){ 
    std::cout << "ERROR: Read ROM - Timeout" << std::endl; 
  }
}

int main(int argc, char* argv[])
{
  bool sflag = false, tflag = false;
  int  num   = 0;
  int  opt;

  if (argc < 3) {
    std::fprintf(stderr, "Usage: %s -s <times> | -t <gpio>\n", argv[0]);
    return -1;
  }

  while ((opt = getopt(argc, argv, "s:t:")) != -1) {
    switch (opt) {
      case 's': sflag = true; num = std::atoi(optarg); break;
      case 't': tflag = true; num = std::atoi(optarg); break;
      default:
        std::fprintf(stderr, "Usage: %s -s <times> | -t <gpio>\n", argv[0]);
        return -1;
    }
  }

  // Build the connection-file path
  std::string connFile =
    "/home/cmx/mtd-emp-toolbox/mtd-daq/"
    "lpGBTv2_3_SO1_ceacmsfw_250603_1554_ETL/"
    "hls_connections.xml";

  // Initialize uHAL
  uhal::ConnectionManager cm("file://" + connFile);
  uhal::HwInterface hw = cm.getDevice("x0");

  // --------------------------------------------
  // debug: print all node IDs
  // for ( auto& nodeName : hw.getNodes() ) {
  //   std::cout << "  • " << nodeName << "\n";
  // }
  // --------------------------------------------

  emp::SCCICNode ic( hw.getNode("datapath.region.fe_mgt.data_framer.scc.ic.auto") );
  ic.reset();                
  usleep(10000);

  // --------------------------------------------
  // debug: try to read rom reg 
  // for (uint8_t a = 0x60; a <= 0x77; ++a)
  // {
  //   try {
  //     ic.icRead(ROM, a);           // ROM = 0x1D7
  //     std::cout << "lpGBT present at 0x"
  //               << std::hex << int(a) << "\n";
  //   } catch (const emp::ICTimeOut&) {
  //     std::cout << "lpGBT not present at 0x"
  //               << std::hex << int(a) << "\n";
  //   }
  // }
  // --------------------------------------------

  if (sflag) {
    unsigned addr; int invert;
    std::printf("Enter lpGBT address (e.g., 0x73): ");
    std::scanf("%x", &addr);
    std::printf("Invert? (1=yes, 0=no): ");
    std::scanf("%d", &invert);

    for (int i = 0; i < num; ++i) {
      tamaleroSetUp(ic, addr, invert != 0);
      usleep(10000);
    }
  }
  else if (tflag) {
    unsigned addr; int delay_s, times;
    std::printf("Enter lpGBT address (e.g., 0x73): ");
    std::scanf("%x", &addr);
    std::printf("Enter delay in seconds: ");
    std::scanf("%d", &delay_s);
    std::printf("Enter number of toggles: ");
    std::scanf("%d", &times);

    toggleTest(ic, delay_s, times, addr, num);
  }

  return 0;
}
