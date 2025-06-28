.PHONY : clean

CXX=g++

CPPFLAGS= -fPIC -g -Wall -I. -I./libusb-1.0 -I./spdlog
LDFLAGS= -shared

OBJECTS=$(SOURCES:.cpp=.o)

TARGET=libpiusb.so

all: $(TARGET)

clean:
	rm -f libpiusb.so align dls motor step libdls.so

install: 
	cp libpiusb.so /usr/lib/libpiusb.so
	chmod 755 /usr/lib/libpiusb.so
	cp piusb.hpp /usr/include/piusb.hpp
	chmod 644 /usr/include/piusb.hpp

	cp dls /usr/bin/dls
	cp libdls.so /usr/lib/libdls.so
	cp dls.hpp /usr/include/dls.hpp

	cp align /usr/bin/align
	cp aligner.hpp /usr/include/aligner.hpp

exe: 
	$(CXX) $(CPPFLAGS) libdls.cpp kbhit.c -fPIC -g -o libdls.so -shared
	$(CXX) $(CPPFLAGS) -o dls -g dls.cpp -L. -ldls
	$(CXX) $(CPPFLAGS) -Wall -g align.cpp aligner.cpp -o align  -lpiusb
	$(CXX) $(CPPFLAGS)  -Wall motor.cpp -o motor -lpiusb
	$(CXX) $(CPPFLAGS) -Wall step.cpp -o step -lpiusb

$(TARGET) : $(OBJECTS)
	$(CXX) $(CPPFLAGS) libpiusb.cpp -fPIC -g -L. -o libpiusb.so -lusb-1.0 -shared

