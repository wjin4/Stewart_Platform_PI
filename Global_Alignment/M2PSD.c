//BOARD #1, TARGET #122, ttyACM0

#include <errno.h>
#include <termios.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>

int kbhit(void); 


double alphax_neg[2] = {-9.909807, -9.794860};
double alphax_pos[2] = {-9.906882, -9.771347};
double alphay_neg[2] = {10.103729, 10.016967}; 
double alphay_pos[2] = {10.142797, 9.933996};


double betax [2]     =  {0.007212, 0.021057};
double betay [2]     =  {0.100659, 0.098714};


double theta [2]     =  {0,0};

int set_interface_attribs (int fd, int speed, int parity); 
void set_blocking (int fd, int should_block); 

int main(int argc, char* argv[]) {

	char *portname = "/dev/ttyACM0";
	int fd = open (portname, O_RDWR | O_NOCTTY | O_SYNC);
	if (fd < 0)
	{
		printf ("error %d opening %s: %s", errno, portname, strerror (errno));
		return;
	}

	set_interface_attribs (fd, B115200, 0);  // set speed to 115,200 bps, 8n1 (no parity)
	set_blocking (fd, 0);                    // set no blocking

	double x[2],y[2];
	double x_tmp, y_tmp; 
	double temperature; 

	int meas[2] = {0,0}; 

	int ipsd; 
	char buf[110]; 

	while (1) {
		if (kbhit()) return; 
		memset (buf, 0, sizeof buf); 

		// read one byte
		char tmp[] = "X";
		int n = read (fd, tmp, 1);

		// align on opening
		int count=0; 
		if (tmp[0] == '\n') {
			while (count < 48) { 
				n = read (fd, tmp, 1); 
				if (n==1) {
					buf[count] = tmp[0]; 
					count+=1;
				}	
			}
			count=0; 


			n = sscanf(buf, "%lf %lf %lf %lf %lf", &x[0], &y[0], &x[1], &y[1], &temperature); 

			int i; 
			for (i=0; i<2; i++) {				
				if (x[i]<0) x[i] = (x[i]-betax[i])*alphax_neg[i]; 
				else        x[i] = (x[i]-betax[i])*alphax_pos[i]; 
				if (y[i]<0) y[i] = (y[i]-betay[i])*alphay_neg[i]; 
				else        y[i] = (y[i]-betay[i])*alphay_pos[i]; 
			}

			printf("% 9.5f % 9.5f % 9.5f % 9.5f % 5.2f\n", x[0], y[0], x[1], y[1], temperature);	
		}
	}
}

int set_interface_attribs (int fd, int speed, int parity)
{
	struct termios tty;
	memset (&tty, 0, sizeof tty);
	if (tcgetattr (fd, &tty) != 0)
	{
		printf ("error %d from tcgetattr", errno);
		return -1;
	}

	cfsetospeed (&tty, speed);
	cfsetispeed (&tty, speed);

	tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;     // 8-bit chars
	// disable IGNBRK for mismatched speed tests; otherwise receive break
	// as \000 chars
	tty.c_iflag &= ~IGNBRK;         // disable break processing
	tty.c_lflag = 0;                // no signaling chars, no echo,
	// no canonical processing
	tty.c_oflag = 0;                // no remapping, no delays
	tty.c_cc[VMIN]  = 0;            // read doesn't block
	tty.c_cc[VTIME] = 20;            // 0.5 seconds read timeout

	tty.c_iflag &= ~(IXON | IXOFF | IXANY); // shut off xon/xoff ctrl

	tty.c_cflag |= (CLOCAL | CREAD);// ignore modem controls,
	// enable reading
	//tty.c_cflag &= ~(PARENB | PARODD);      // shut off parity
	tty.c_cflag &= ~(PARENB);      // shut off parity
	tty.c_cflag &= ~CSTOPB;
	tty.c_cflag |= parity;
	tty.c_cflag &= ~CRTSCTS;
	tty.c_lflag |= ICANON; // Canonical Mode
	tty.c_iflag |= IGNCR; // Ignore carriage returns

	cfmakeraw (&tty);
	tcflush(fd,TCIFLUSH);

	if (tcsetattr (fd, TCSANOW, &tty) != 0)
	{
		printf ("error %d from tcsetattr", errno);
		return -1;
	}
	return 0;
}

void set_blocking (int fd, int should_block)
{
	struct termios tty;
	memset (&tty, 0, sizeof tty);
	if (tcgetattr (fd, &tty) != 0)
	{
		printf ("error %d from tggetattr", errno);
		return;
	}

	tty.c_cc[VMIN]  = should_block ? 1 : 0;
	tty.c_cc[VTIME] = 5;            // 0.5 seconds read timeout

	if (tcsetattr (fd, TCSANOW, &tty) != 0)
		printf ("error %d setting term attributes", errno);
}


#include <fcntl.h>   // For file handling
#include <termios.h> // Terminal IO
#include <stdio.h>
#include <unistd.h>

int kbhit(void)
{
    struct termios oldt, newt;
    int ch;
    int oldf;

    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);

    ch = getchar();

    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    fcntl(STDIN_FILENO, F_SETFL, oldf);


    if (ch=='q') {
        ungetc(ch, stdin);
	return 1; 
    }

//    if(ch != EOF)
//    {
//        ungetc(ch, stdin);
//        return 1;
//    }


    return 0;
}
