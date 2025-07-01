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
  ic.icWrite(dirReg, bit, addr);

  uint8_t value = 0;
  for (int i = 0; i < times; ++i) {
    value ^= 1;
    ic.icWrite(outReg, value, addr);
    sleep(delay_s);
  }
}

void tamaleroSetUp(emp::SCCICNode& ic,
                   unsigned addr,
                   bool invert)
{
  ic.icWrite(ULDATASOURCE0, 0xC0, addr);
  usleep(10000);
  ic.icWrite(ULDATASOURCE0, 0x00, addr);

  if (invert) ic.icWrite(CHIPCONFIG, 0x80, addr);

  ic.icWrite(POWERUP2, 0x06, addr);
  usleep(10000);

  uint8_t romval = ic.icRead(ROM, addr);
  printf("ROM register value: 0x%02X\n", romval);
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
  uhal::HwInterface        hw = cm.getDevice("x0");
  emp::SCCICNode           ic( hw.getNode("SCCIC") );

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