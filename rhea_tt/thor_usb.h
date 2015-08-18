/************************************************************************/
/* thor_usb.h								*/
/*                                                                      */
/* Header file for the Thorlabs USB camera.				*/
/************************************************************************/
/*                                                                      */
/* Authors : Theo ten Brummelaar and Michael Ireland                    */
/* Date    : July 2015	                                                */
/************************************************************************/

#ifndef __THOR_USB__
#define __THOR_USB__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <zlib.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <pthread.h>
#include <time.h>
#include <fitsio.h>
#include <stdbool.h>


struct s_usb_camera {
	float fps; /* The number of frames per second asked for */
	float  real_fps;
	float   exptime;
	float  proc_fps;
	float	min;
	float	max;
	float	x_mult;
	float	y_mult;
	int	num_lenslets;
	int gain;
	int x;
	int y;
	int dx;
	int dy;
	int pixelclock;
	int destripe;
	int overlay_boxes;
	int running;
	int usb_disp_x;
	int usb_disp_y;
	int centroid_box_width;
			  };

extern struct s_usb_camera usb_camera;


/* thor_usb.c */
bool usb_cammera_is_running(void);
int open_usb_camera(void);
int close_usb_camera(void);
void *do_usb_camera(void *arg);
void set_usb_camera_callback(void (*new_camera_callback)(
					time_t time_stamp, float *image,
                                        int width, int height));
//int start_usb_camera_display(int argc, char **argv);
//int stop_usb_camera_display(int argc, char **argv);
int set_usb_camera_aoi(int x, int y, int width, int height);
void get_usb_camera_aoi(int *x, int *y, int *width, int *height);
double set_frame_rate(double fps);
int set_pixelclock(unsigned int new_pixelclock);
int usb_camera_set_gain(int new_gain);
int create_dark(void);
int zero_dark(void);
void complete_fits_cube(void);
double usb_camera_set_exptime(double exptime);
int send_labao_set_usb_camera(bool send_to_all_clients);
bool usb_cammera_is_running(void);
int set_num_sum_frame(int num);

int cmd_dark(int argc, char **argv);
int cmd_itime(int argc, char **argv);
int cmd_setnframe(int argc, char **argv);
int cmd_startcam(int argc, char **argv);
int cmd_stopcam(int argc, char **argv);
int cmd_zdark(int argc, char **argv);
int cmd_save(int argc, char **argv);
int cmd_savecube(int argc, char **argv);
int cnd_dark(int argc, char **argv);
int cmd_camgain(int argc, char **argv);
int cmd_destripe(int argc, char **argv);
int cmd_pixelclock(int argc, char **argv);
int cmd_aoi(int argc, char **argv);
int cmd_optimalcam(int argc, char **argv);
int cmd_fps(int argc, char **argv);
int cmd_image(int argc, char **argv);

void bgnd_usb_camera(void);
void bgnd_complete_fits_cube(void);
#endif
