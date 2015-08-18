all: rhea_tt

thor_usb.o: thor_usb.c thor_usb.h
	gcc -O2 -march=armv6zk -mcpu=arm1176jzf-s -c -g thor_usb.c

u6.o: u6.c u6.h
	gcc -c -g u6.c

u6_util.o: u6_util.c u6.h
	gcc -c -g u6_util.c

uicoms.o: uicoms.c uicoms.h
	gcc -c -g uicoms.c

rhea_tt.o: rhea_tt.c
	gcc -O2 -march=armv6zk -mcpu=arm1176jzf-s -c -g rhea_tt.c

rhea_tt: rhea_tt.o uicoms.o thor_usb.o u6_util.o u6.o
	gcc -O2 -march=armv6zk -mcpu=arm1176jzf-s -o rhea_tt rhea_tt.o uicoms.o thor_usb.o u6_util.o u6.o -lueye_api -lcfitsio -lz -llabjackusb -lpthread -lm

clean: 
	rm *.o
	rm rhea_tt
