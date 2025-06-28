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
	
	int step = atoi(argv[2]);
	int velocity = 10;
	Motor motor;
	motor.setVelocity(velocity);
	int current_pos = motor.getPosition();
	int new_pos = current_pos + step;
	motor.setPosition(new_pos);
	cout << "Position set: " << motor.getPosition() << endl;
	return 0;
}
