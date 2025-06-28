#include <piusb.hpp>
#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

using namespace std;



int error(){
	cout << "usage: ./motor position\nposition = ???\n";
	return 0;
}



int main(int argc, const char *argv[])
{
	if (argc < 2) return error();

	int velocity = 10;
	int position = atoi(argv[1]);
	Motor motor;
	motor.setVelocity(velocity);
	cout << "Got position: " << position << endl;
	motor.setPosition(position);
	cout << "Position set: " << motor.getPosition() << endl;
	return 0;
}

