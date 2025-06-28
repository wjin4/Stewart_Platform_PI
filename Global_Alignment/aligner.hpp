#include <libusb-1.0/libusb.h>

class Align
{
	public:
		Align();
		~Align();

		void sLaserOn();
		void sLaserOff();
		void powerOn();
		void powerOff();
		void shutterCalibrate();	
		void shutterOpen();
		void shutterClose();
		void mirrorCalibrate();
		void mirrorStep(int step);
		void mirrorPos(int pos);
		int help();
	private:
		const static int _a = 0;
		const static int _b = 1030;
		const static int _c = 2070;
};


