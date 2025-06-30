#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>

#define MASTER_ADDR 0x73
#define SERVANT_ADDR 0x70

#define PIO_DIR_HI 0x053
#define PIO_DIR_LO 0x054

#define OUT_HI 0x055
#define OUT_LO 0x056

#define ULDATASOURCE0 0x128
#define CHIPCONFIG 0x036
#define POWERUP2 0x0fb
#define ROM 0x1d7

void toogleTest(int delay, int times, unsigned addr, unsigned gpio){
	// Find correct reg and data
	unsigned dirReg = (gpio < 8) ? PIO_DIR_LO : PIO_DIR_HI;
    unsigned outReg = (gpio < 8) ? OUT_LO     : OUT_HI;
    uint8_t bit = 1 << (gpio % 8);

	// Set GPIO pin as output
	icWrite(dirReg, bit, addr);

	// Toggle the gpio pin HIGH then Low
	uint8_t value = 0;
	for (int i=0; i<times;i++){
		value = value ^ 1;
		icWrite(outReg, value, addr);
		sleep(delay);
	}
	return;
}

void tamaleroSetUp(unsigned addr, bool invert){
	// Toggle Uplink data path test patterns
	icWrite(ULDATASOURCE0, 0xC0, addr);
	usleep(10000); 
	icWrite(ULDATASOURCE0, 0x0, addr);

	// Set highSpeedDataOutInvert to 1
	if (invert) icWrite(CHIPCONFIG, 0x80, addr);

	// Power up lpGBT
	icWrite(POWERUP2, 0x06, addr);
	usleep(10000); 

	uint8_t romval = icRead(ROM, addr);
	printf("ROM register value: 0x%02X\n", romval);
	
	return;
}

int main(int argc, char* argv[]){
	int opt;
    bool sflag = false, tflag = false;
    int num = 0;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s -s <times> | -t <gpio>\n", argv[0]);
        return -1;
    }

    // Parse command-line options
    while ((opt = getopt(argc, argv, "s:t:")) != -1) {
        switch (opt) {
            case 's':
                sflag = true;
                num   = atoi(optarg);
                break;
            case 't':
                tflag = true;
                num   = atoi(optarg);
                break;
            default:
                fprintf(stderr, "Usage: %s -s <times> | -t <gpio>\n", argv[0]);
                return -1;
        }
    }

    if (sflag) {
        unsigned addr;
        int invert;
        printf("Enter I2C address (e.g., 0x73): ");
        scanf("%x", &addr);
        printf("Invert? (1=yes, 0=no): ");
        scanf("%d", &invert);

        for (int i = 0; i < num; i++) {
            tamaleroSetUp(addr, invert ? true : false);
            usleep(10000);
        }
    }
    else if (tflag) {
        unsigned addr;
        int delay, times;
        printf("Enter I2C address (e.g., 0x73): ");
        scanf("%x", &addr);
        printf("Enter delay in seconds: ");
        scanf("%d", &delay);
        printf("Enter number of toggles: ");
        scanf("%d", &times);

        toogleTest(delay, times, addr, num);
    } else {
        fprintf(stderr, "Usage: %s -s <times> | -t <gpio>\n", argv[0]);
        return -1;
    }

    return 0;
}