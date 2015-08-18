/************************************************************************/
/* thor_usb.c	              						*/
/*    									*/
/* Routines for getting data from the USB camera.			*/
/************************************************************************/
/*    									*/
/* Authors : Theo ten Brummelaar and Michael Ireland	                */
/* Date    : July 2015							*/
/************************************************************************/

#include <ueye.h>
#define LONGLONG_TYPE
#include "uicoms.h"
#include "thor_usb.h"

#define LONGLONG_TYPE /* There is a conflict on this fitsio.h ands ueye.h */

/* How many frames do we need in the ring buffer? */

#define NUM_IMAGE_MEM 	50
#define USB_DISP_X	320
#define USB_DISP_Y	256 /* !!! Must be a multiple of 2 */
#define MAX_FILE_NUMBER	999
#define SECS_FOR_PROC  2
#define NUM_MIN 4 /*The number of minimum pixels in each row to average over */

struct s_usb_camera usb_camera;
static char fits_filename[2000];
static bool save_fits_file = FALSE;
static float *data_frames[NUM_IMAGE_MEM];
static float *dark;
static float *sum_frame;
static float *this_frame;
static int num_sum_frame = 1;
static int count_sum_frame = 0;
static int current_data_frame_ix=0;
static unsigned int last_max=0, last_min=0, last_mean=0;
static UEYE_CAMERA_LIST *cam_list;
static HIDS	cam_pointer;
static HWND	cam_window;
static SENSORINFO cam_info;
static IS_RECT 	rectAOI;
static IS_POINT_2D	pos_inc;
static IS_POINT_2D	size_inc;
static IS_POINT_2D	size_min;
static int	pid_image_memory[NUM_IMAGE_MEM];
static char	*image_memory[NUM_IMAGE_MEM];
static float	*image_data_cube = NULL;
static float	*image_data_cube_pointer = NULL;
static int 	image_data_cube_num_frames = 0;
static int 	image_data_cube_count_frames = 0;
static bool	usb_camera_open = FALSE;
static pthread_mutex_t usb_camera_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_t usb_camera_thread;
static bool usb_camera_running = FALSE;
static int usb_camera_num_frames = 0;
static int usb_camera_last_num_frames=0;
static void (*usb_camera_callback)(time_t time_stamp,
		float *data, int width, int height) = NULL;
static time_t usb_camera_last_proc_sec = 0;
//static Window usb_camera_window;
//static XImage *usb_camera_ximage = NULL;
static bool usb_camera_display = FALSE;
static void *usb_camera_image;
static time_t usb_camera_display_start = 0;
static int usb_camera_display_frames = 0;
static bool usb_camera_local_display = FALSE;
static int data_record_start = 0;
static int data_record_stop = 0;

/************************************************************************/
/* open_usb_camera()							*/
/*									*/
/* Tries to open a conenction the USB camera and find out what it can	*/
/* do.									*/
/* Returns error level.							*/
/************************************************************************/

int open_usb_camera(void)
{
	int	i, j;
	int	dw;
	int	bits_per_pixel;
	int	num_cams;
	double  ferr;

	/* Close it first if we need to */

	if (usb_camera_open) close_usb_camera();

	/* By default we destripe and show the boxes */

	usb_camera.overlay_boxes = TRUE;
	usb_camera.destripe = TRUE;

	/* How many cameras are there out there? */

	if (is_GetNumberOfCameras(&num_cams))
	{
		return error(ERROR,"Failed to get number of cameras.\n");
	}

	if (num_cams == 1)
		error(MESSAGE, "Found %d camera.\n", num_cams);
	else
		error(MESSAGE, "Found %d cameras.\n", num_cams);

	if (num_cams < 1) return error(ERROR,"Found no cameras.");

	/* Get the list of cameras */

	cam_list = (UEYE_CAMERA_LIST *)malloc(sizeof(UEYE_CAMERA_LIST));
	if (is_GetCameraList(cam_list))
	{
		return error(ERROR,"Failed to get camera list.\n");
	}

	/* How many cameras? */

	dw = cam_list->dwCount;

	/* Now get the correct amount of space for the camera info */

	free(cam_list);
	cam_list = (UEYE_CAMERA_LIST *)malloc(sizeof(DWORD) + 
			dw * sizeof(UEYE_CAMERA_INFO));
	cam_list->dwCount = dw;

	if (is_GetCameraList(cam_list))
	{
		return error(ERROR,"Failed to get camera list.\n");
	}

	/* 
  	 * Open the camera... should be in the same thread as 
  	 * SetDisplayMode() and ExitCamera()
  	 * We may have to do tricky things with is_SetCameraID when we
  	 * have more than one camera.
 	 */

	cam_pointer = (HIDS)0x1; /* With luck, this is the right camera */
	if ((i = is_InitCamera(&cam_pointer, &cam_window)))
	{
		return error(ERROR,
			"Failed to open camera connection (%d).\n",i);
	}

	/* Get the information about the camera sensor */

	if ((i = is_GetSensorInfo(cam_pointer, &cam_info)))
	{
		close_usb_camera();
		return error(ERROR,
			"Failed to get sensor information (%d).\n",i);
	}

	/* Allocate the memory, now that we have this basic info. */

	for (i=0;i<NUM_IMAGE_MEM;i++)
		data_frames[i] = malloc(cam_info.nMaxWidth*cam_info.nMaxHeight*sizeof(float));
	dark = malloc(cam_info.nMaxWidth*cam_info.nMaxHeight*sizeof(float));
	sum_frame = malloc(cam_info.nMaxWidth*cam_info.nMaxHeight*sizeof(float));
	this_frame = malloc(cam_info.nMaxWidth*cam_info.nMaxHeight*sizeof(float));

	for (i=0;i<cam_info.nMaxHeight;i++)
	for (j=0;j<cam_info.nMaxWidth;j++) dark[i*cam_info.nMaxWidth + j]=0.0;

	bits_per_pixel = 8;

	/* Allocate Memory for Images. This is done based on a full frame. */

	for(j = 0; j< NUM_IMAGE_MEM; j++)
	{
	    if ((i = is_AllocImageMem(cam_pointer,  
			cam_info.nMaxWidth, cam_info.nMaxHeight,
			bits_per_pixel, 
			&(image_memory[j]), &(pid_image_memory[j]))))
	    {
		close_usb_camera();
		return error(ERROR,"Failed to get image memory (%d).\n",i);
	    }
	
	    /* Make this part of the sequence in the ring buffer */

	    if ((i = is_AddToSequence(cam_pointer, 
			image_memory[j], pid_image_memory[j])))
	    {
		close_usb_camera();
		return error(ERROR,
		"Failed to add image memory to sequence (%d).\n", i);
	    }
	}

	usb_camera_open = TRUE;
	
	/* What are we able to do in terms of AOI? */

	if ((i = is_AOI(cam_pointer,  IS_AOI_IMAGE_GET_POS_INC,
				&pos_inc, sizeof(pos_inc))))
	{
		close_usb_camera();
		return error(ERROR,
			"Failed to get position incriment (%d).\n",i);
	}
	
	if ((i = is_AOI(cam_pointer,  IS_AOI_IMAGE_GET_SIZE_INC,
				&size_inc, sizeof(size_inc))))
	{
		close_usb_camera();
		return error(ERROR,
			"Failed to get size incriment (%d).\n",i);
	}
	
	if ((i = is_AOI(cam_pointer,  IS_AOI_IMAGE_GET_SIZE_MIN,
				&size_min, sizeof(size_min))))
	{
		close_usb_camera();
		return error(ERROR,
			"Failed to get size incriment (%d).\n",i);
	}
	
	/* Default is the whole camera */

	rectAOI.s32X = 0;
	rectAOI.s32Y = 0;
	rectAOI.s32Width = cam_info.nMaxWidth;
	rectAOI.s32Height = cam_info.nMaxHeight;
	
	if ((i = is_AOI(cam_pointer,  IS_AOI_IMAGE_SET_AOI,
				&rectAOI, sizeof(rectAOI))))
	{
		close_usb_camera();
		return error(ERROR,"Failed to set AOI (%d).\n",i);
	} 

	/* With luck that worked */

	if ((i = is_AOI(cam_pointer,  IS_AOI_IMAGE_GET_AOI,
					&rectAOI, sizeof(rectAOI))))
	{
		close_usb_camera();
		return error(ERROR,"Failed to get AOI (%d).\n",i);
	}

	error(MESSAGE,
		"Camera set to %dx%d pixels. Pos inc %dx%d Size in %dx%d",
			rectAOI.s32Width, rectAOI.s32Height,
			pos_inc.s32X, pos_inc.s32Y,
			size_inc.s32X, size_inc.s32Y);

	/* Set Gain Boost off. This increased gain also increases pattern
	   noise in the dark, which can't be destriped. */

	if ((i = is_SetGainBoost(cam_pointer, IS_SET_GAINBOOST_OFF)))
	{
		close_usb_camera();
		return error(ERROR, "Failed to set Gain Boost on.");
	}	

	/* Set Hardware Gain to Maximum. */

	if (usb_camera_set_gain(100))
	{
		close_usb_camera();
		return error(ERROR, "Failed to set camera gain.");
	}

	/* Set Hardware Gain to Maximum. */

	if (set_pixelclock(43))
	{
		close_usb_camera();
		return error(ERROR, "Failed to set camera pixelclock.");
	}

	/* How many bits per pixel? */

	if ((i = is_SetColorMode(cam_pointer,  IS_CM_SENSOR_RAW8)))
	{
		close_usb_camera();
		return error(ERROR,"Failed to set color mode (%d).\n",i);
	}

	/* Setup an event for the frames */

	if ((i = is_EnableEvent(cam_pointer, IS_SET_EVENT_FRAME_RECEIVED)))
	{
		close_usb_camera();
		return error(ERROR,"Failed to enable the event (%d).\n", i);
	}
	
	/* Create  Mutex for this */

	if (pthread_mutex_init(&usb_camera_mutex, NULL) != 0)
		error(FATAL, "Unable to create USB camera mutex.");

	/* Create thread to handle USB data */

	if (pthread_create(&usb_camera_thread, NULL, do_usb_camera, NULL) != 0)
	{
		return error(FATAL, "Error creating TV tracking thread.");
	}

	/* Set Frames per Sec to 200 */

	if ( (ferr=set_frame_rate(200.0)) < 0.0 )
	{
		close_usb_camera();
		return error(ERROR,
			"Failed to set frame rate. Errror %3.2lf", ferr);
	}

	/* That should be it */

	return NOERROR;

} /* open_usb_camera() */
	
/************************************************************************/
/* close_usb_camera()							*/
/*									*/
/* Tries to close the conenction the USB camera.			*/
/* Returns error level.							*/
/************************************************************************/

int close_usb_camera(void)
{
	int	i,j;

	/* Stop the camera if it is running */

	error(MESSAGE,"Stopping the USB Camera.");
	cmd_stopcam(0, NULL); 
	
	/* Stop the thread */

	error(MESSAGE,"Waiting for USB Camera thread to terminate.");
	usb_camera_open = FALSE;

	if (pthread_join(usb_camera_thread,NULL) != 0)
	{
		return error(ERROR,
			"Error waiting for USB camera thread to stop.");
	}

	/* Remove the event */

	error(MESSAGE,"Disabling USB Camera.");
	if ((i = is_DisableEvent(cam_pointer, IS_SET_EVENT_FRAME_RECEIVED)))
	{
		return error(ERROR,"Failed to disable the event (%d).\n", i);
	}
	
	/* Release image memory */

	error(MESSAGE,"Releasing Camera Memory.");
	for (i=0;i<NUM_IMAGE_MEM;i++) free(data_frames[i]);

	free(dark);
	free(sum_frame);
	free(this_frame);

	for(j = 0; j< NUM_IMAGE_MEM; j++)
	{
	    if ((i = is_FreeImageMem(cam_pointer,
			image_memory[j], pid_image_memory[j])))
	    {
		return error(ERROR,"Failed to free image memory (%d).\n",i);
	    }
	}
	free(cam_list);

	/* Close camera conenction */

	error(MESSAGE,"Closing USB Camera.");
	if (is_ExitCamera(cam_pointer))
	{
		return error(ERROR,"Failed to close camera connection.\n");
	}

	return NOERROR;
}

/************************************************************************/
/* do_usb_camera()							*/
/*    									*/
/* Runs as a separrate thread and tries to keep up with the usb camera. */
/************************************************************************/

void *do_usb_camera(void *arg)
{
	unsigned char *p;
	float min_pixels[NUM_MIN];
	float row_min;
	int i,j,k,l;
	static float *data;

	while(usb_camera_open)
	{

		/* Is there anything there? */

		if (!usb_camera_open || !usb_camera_running ||
		     is_WaitEvent(cam_pointer, IS_SET_EVENT_FRAME_RECEIVED, 0))
		{
			usleep(1000);
			continue;
		}

		/* Lock the mutex */

		pthread_mutex_lock(&usb_camera_mutex);

		/* Get the current image */

		if (is_GetImageMem(cam_pointer, &usb_camera_image))
		{
			pthread_mutex_unlock(&usb_camera_mutex);
			usleep(1000);
			continue;
		}

                /*
                 * Transfer the image to the float array, 
                 * computing values for destriping
                 */
		last_max=0;
		last_min=255;
		last_mean=0;
                for(j =0, p = usb_camera_image; j< rectAOI.s32Height; j++)
                {
                        for(k=0;k<NUM_MIN;k++) min_pixels[k]=255;
                        for(i=0; i< rectAOI.s32Width; i++)
                        {
			                /* First, deal with basic stats */
			                if (*p>last_max) last_max=*p;
			                if (*p<last_min) last_min=*p;
			                last_mean += *p;
			                /* Now the destriping algorithm */
                            if(*p < min_pixels[NUM_MIN-1])
                            {

                                /* 
                                 * Find the index to insert the 
                                 * darkpixel value
                                 */

                                l = 0;
                                while(min_pixels[l] < *p) l++;

                                /* Shift the current values along one */

                                for(k=NUM_MIN-1;k>l;k--)
                                        min_pixels[k] = min_pixels[k-1];

                                /* Insert the new min pixel */

                                min_pixels[k] = *p;
                            }
                            this_frame[j*rectAOI.s32Width + i] = (float)*p++;
                        }
                        for(;i < cam_info.nMaxWidth; i++) p++;

                        /* If needed, try to destripe */

                        if (usb_camera.destripe)
                        {
                                row_min=0;
                                for (k=0; k<NUM_MIN; k++)
                                        row_min += (float)min_pixels[k];
                                row_min /= NUM_MIN;
                                for (i=0; i<rectAOI.s32Width;i++)
                                        this_frame[j*rectAOI.s32Width + i] -= row_min;
                        }
                }
		last_mean /= rectAOI.s32Width;
		last_mean /= rectAOI.s32Height;

		/* Sum this frame in? */

                for(j =0; j < rectAOI.s32Height; j++)
                {
                    for(i=0; i < rectAOI.s32Width; i++)
                    {
			sum_frame[j*rectAOI.s32Width + i] += this_frame[j*rectAOI.s32Width + i];
		    }
		}

		/* Is that it? */

		if (++count_sum_frame < num_sum_frame)
		{
			pthread_mutex_unlock(&usb_camera_mutex);
			usleep(1000);
			continue;
		}
		
                /* We got a frame! */

                usb_camera_num_frames++;
		count_sum_frame = 0;

                /* 
                 * Now that the data is transferred, increment the data pointer 
                 * NB this is inside the mutex.
                 */

                current_data_frame_ix++;
                current_data_frame_ix = current_data_frame_ix % NUM_IMAGE_MEM;
                data =  data_frames[current_data_frame_ix];

                for(j =0; j < rectAOI.s32Height; j++)
                {
                    for(i=0; i < rectAOI.s32Width; i++)
                    {
			data[j*rectAOI.s32Width + i] = sum_frame[j*rectAOI.s32Width + i]/num_sum_frame - dark[j*rectAOI.s32Width + i];
			sum_frame[j*rectAOI.s32Width + i] = 0.0;
		    }
		}

		/* Save this to the data cube if we need to */

		if (image_data_cube_num_frames > 0 &&
	            image_data_cube_count_frames < image_data_cube_num_frames &&
		    image_data_cube_pointer != NULL)
		{
		    if (image_data_cube_count_frames == 0)
			data_record_start = time(NULL);

		    for(j = 0; j < rectAOI.s32Height; j++)
		    for(i = 0; i < rectAOI.s32Width; i++)
			*image_data_cube_pointer++ = data[j*rectAOI.s32Width + i];

		    if (++image_data_cube_count_frames == 
			image_data_cube_num_frames)
				data_record_stop = time(NULL);
		}

		/* Is there a callback function? */

		if (usb_camera_callback != NULL)
		{
			(*usb_camera_callback)(
				time(NULL), data, 
				rectAOI.s32Width, rectAOI.s32Height);
		}

		/* Unlock this for the next one */

		is_UnlockSeqBuf(cam_pointer, IS_IGNORE_PARAMETER, 
			usb_camera_image);
		
		/* Unlock the mutex */

		pthread_mutex_unlock(&usb_camera_mutex);
	}

	return NULL;

} /* do_usb_camera() */

/************************************************************************/
/* set_usb_camera_callback()						*/
/*									*/
/* Sets up the callback. Send NULL if you want to turn off teh callback.*/
/************************************************************************/

void set_usb_camera_callback(void (*new_camera_callback)(time_t time_stamp,
					float *data, 
					int aoi_width, int aoi_height))
{
	usb_camera_callback = new_camera_callback;

} /* set_usb_camera_callback() */

/************************************************************************/
/* start_usb_camera()							*/
/*									*/
/* Set the camera running.						*/
/* Returns error level.							*/
/************************************************************************/

int cmd_startcam(int argc, char **argv)
{
	int 	i;

	/* Are we already running? */

	if (usb_camera_running) return NOERROR;

	/* We will use an image queue */

	if ((i = is_InitImageQueue(cam_pointer, 0)))
	{
		close_usb_camera();
	  return error(ERROR, "Failed to enable image queue (%d).\n", i);
	}

	/* Start capturing video */

	if ((i = is_CaptureVideo(cam_pointer, IS_WAIT)))
	{
	     return error(ERROR,"Failed to capture video (%d).\n", i);
	}

	/* Wait for an even second */

	usb_camera_last_proc_sec = time(NULL);
	while (usb_camera_last_proc_sec == time(NULL));
	usb_camera_last_proc_sec = time(NULL);
	usb_camera_num_frames = 0;
	usb_camera_last_num_frames = 0;

	/* OK, we're running */

	usb_camera_running = TRUE;

	return NOERROR;

} /* start_usb_camera() */

/************************************************************************/
/* stop_usb_camera()							*/
/*									*/
/* Stop the camera running.						*/
/* Returns error level.							*/
/************************************************************************/

int cmd_stopcam(int argc, char **argv)
{
	int	i;

	/* Are we even running */

	if (!usb_camera_running) return NOERROR;

	/* Stop Capturing video */

	if ((i = is_StopLiveVideo(cam_pointer, IS_WAIT)))
	{
	     return error(ERROR,"Failed to free image memory (%d).\n",i);
	}

	usb_camera_running = FALSE;
	return NOERROR;

} /* stop_usb_camera() */


/************************************************************************/
/* set_usb_camera_aoi()							*/
/*									*/
/* Set the USB camera area of interest.					*/
/* Returns								*/
/* 0 - All good								*/
/* -1 - Camera is running or no open.					*/
/* -2 - AOI out of bounds.						*/
/* -3 - X Position is not a multiple of what we need.			*/
/* -4 - Y Position is not a multiple of what we need.			*/
/* -5 - X Size is not a multiple of what we need.			*/
/* -6 - Y Size is not a multiple of what we need.			*/
/* -7 - Failed to set AOI.						*/
/************************************************************************/

int set_usb_camera_aoi(int x, int y, int width, int height)
{
	IS_RECT 	newAOI;

	/* This seems unecessary now. */

	/* if (!usb_camera_open || usb_camera_running) return -1; */

	if (x >= cam_info.nMaxWidth || x < 0 || 
		 y >= cam_info.nMaxHeight || y < 0 ||
		 x + width > cam_info.nMaxWidth ||
		 y + height > cam_info.nMaxHeight) return -2;

	if (x % pos_inc.s32X) return -3;
	if (y % pos_inc.s32Y) return -4;
	if (width % size_inc.s32X) return -5;
	if (height % size_inc.s32Y) return -6;
	if (width < size_min.s32X || height < size_min.s32Y) return -7;

	usb_camera.x = newAOI.s32X = x;
	usb_camera.dx = newAOI.s32Y = y;
	usb_camera.y = newAOI.s32Width = width;
	usb_camera.dy = newAOI.s32Height = height;

	if (is_AOI(cam_pointer, IS_AOI_IMAGE_SET_AOI, &newAOI, sizeof(newAOI)))
	{
		return -8;
	}
	
	rectAOI = newAOI;

	return 0;

} /* set_usb_camera_aoi() */

/************************************************************************/
/* get_usb_camera_aoi()							*/
/*									*/
/* Get the USB camera area of interest 					*/
/************************************************************************/

void get_usb_camera_aoi(int *x, int *y, int *width, int *height)
{
	*x = rectAOI.s32X;
	*y = rectAOI.s32Y;
	*width = rectAOI.s32Width;
	*height = rectAOI.s32Height;

} /* get_usb_camera_aoi() */

/************************************************************************/
/* call_set_usb_camera_aoi()						*/
/*									*/
/* User callable version.						*/
/************************************************************************/

int cmd_aoi(int argc, char **argv)
{
	char	s[100];
	int x, y, width, height;

	/* We ignore these checks to make life easier 
	if (!usb_camera_open) return error(ERROR,
		"Can not change AOI unless camera is open.");
		
	if (usb_camera_running) return error(ERROR,
		"Can not change AOI while camera is running.");
	*/

	/* Check out the command line */


	if (argc > 4)
	{
		sscanf(argv[1],"%d",&x);
		sscanf(argv[2],"%d",&y);
		sscanf(argv[3],"%d",&width);
		sscanf(argv[4],"%d",&height);
	}
	else
	{
		return error(ERROR, "Useage: camsetaoi [x] [y] [width] [height]");
	}

	switch(set_usb_camera_aoi(x, y, width, height))
	{
		case 0: return NOERROR;

		case -2: return error(ERROR, "AOI is out of bounds.");

		case -3: return error(ERROR, 
			"X position must be a multiple of %d.", pos_inc.s32X);

		case -4: return error(ERROR, 
			"Y position must be a multiple of %d.", pos_inc.s32Y);

		case -5: return error(ERROR, 
			"Width must be a multiple of %d.", size_inc.s32X);

		case -6: return error(ERROR, 
			"Height must be a multiple of %d.", size_inc.s32Y);

		case -7: return error(ERROR, 
			"Size must be at least %dx%d.", 
			size_min.s32X, size_min.s32Y);

		case -8: return error(ERROR, "Failed to set AOI.");

		case -1:
		default: return error(ERROR,"Odd... we should never get here.");

	}

} /* call_set_usb_cammera_aoi() */

/************************************************************************/
/* set_optimal_camera_timing()		    				*/
/*									*/
/* User callable function to get the max pixel clock rate and the 	*/
/* maximum frame rate.  						*/
/************************************************************************/

int cmd_optimalcam(int argc, char **argv)
{
	int pMaxPxlClk, errcode;
	double pMaxFrameRate;

	if (!usb_camera_open) return error(ERROR,
		"Can not set camera timing unless camera is open.");
		
	if (!usb_camera_running) return error(ERROR,
		"Camera must be running to find optimal timing.");

	/* Run the function */

	if ((errcode=is_SetOptimalCameraTiming(cam_pointer, 
		IS_BEST_PCLK_RUN_ONCE, 10000, &pMaxPxlClk, &pMaxFrameRate)))
	{
		switch(errcode)
		{
			case IS_AUTO_EXPOSURE_RUNNING:
				return error(ERROR,
					"Someone turned on AUTO exposure!");

			case IS_NOT_SUPPORTED:
				return error(ERROR,
		"No fun - this camera doesn't support finding optimal timing.");

			default:
				return error(ERROR, "Unknown Error.");
		}
	}

	/* Output the results */

	error(MESSAGE, "Max Clock: %d. Max Frame Rate: %6.1lf.",
		pMaxPxlClk, pMaxFrameRate);

	return NOERROR;

} /* set_optimal_camera_timing() */

/************************************************************************/
/* set_frame_rate()	    		    				*/
/*									*/
/* Positive Number - Actual frame rate set				*/
/* -1 : Invalid Frame Rate.   						*/
/* -2 : Another error setting frame rate   				*/
/* -3 : An error setting exposure time    				*/
/************************************************************************/

double set_frame_rate(double fps)
{
	double newFPS, dummy_exposure=0.0;
	int errcode;

	if ((errcode = is_SetFrameRate(cam_pointer, fps, &newFPS)) )
	{
		if (errcode == IS_INVALID_PARAMETER)
			return -1.0; 
		else 
			return -2.0;
	}

	/* As recommended in the manual, now set the exposure. */

	if ( (errcode = is_Exposure(cam_pointer, IS_EXPOSURE_CMD_SET_EXPOSURE, 
		&dummy_exposure, sizeof(dummy_exposure))) )
		return -3.0;

	usb_camera.fps = newFPS;

	return (newFPS);

} /* set_frame_rate() */

/************************************************************************/
/* call_set_frame_rate()				    		*/
/*									*/
/* User Callable version of set_frame_rate  				*/
/************************************************************************/

int cmd_fps(int argc, char **argv)
{
	char s[100];
	double input_fps, newFPS;
	if (argc > 1)
	{
		sscanf(argv[1],"%lf",&input_fps);
	}
	else
	{
		return error(ERROR, "Useage: fps [fps]");
	}

	if ((newFPS = set_frame_rate(input_fps)) < 0.0)
	{
		if (newFPS == -1.0)
			return error(ERROR, "Invalid Frame Rate");
		else return error(ERROR, "Unknown error setting Frame Rate");
	}

	error(MESSAGE, "Frames per sec now: %6.1lf", newFPS);

	return NOERROR;
}

/************************************************************************/
/* set_pixelclock()	   		 		    		*/
/*									*/
/* Set the pixel clock rate in MHz 					*/
/* Error -1: Invalid value. 						*/
/* Error -2: Another error.						*/
/************************************************************************/

int set_pixelclock(unsigned int new_pixelclock)
{
	int errcode;
	double dummy_exposure=0.0;
	
	if ( (errcode = is_SetPixelClock(cam_pointer, new_pixelclock)) ){
		if (IS_INVALID_PARAMETER) return -1;
		else return -2;
	}

	/* As recommended in the manual, now set the exposure. */

  	 if ( (errcode = is_Exposure(cam_pointer, IS_EXPOSURE_CMD_SET_EXPOSURE, 
		&dummy_exposure, sizeof(dummy_exposure))) )
			return -3;

	usb_camera.pixelclock = new_pixelclock;

	return 0;

} /* set_pixelclock() */

/************************************************************************/
/* call_set_pixelclock()	 		    	 		*/
/*									*/
/* User callable version of set_pixelclock.				*/
/************************************************************************/

int cmd_pixelclock(int argc, char **argv)
{
	int errcode;
	int input_pixelclock, min_clock, max_clock;
	char instructions[80], s[80];

	/* Fist, get the range of supported pixel clocks */

	if ( (errcode = is_GetPixelClockRange(cam_pointer, 
		&min_clock, &max_clock)) )
		return error(ERROR, "Could not get Pixelclock range");

	if (argc > 1)
	{
		sscanf(argv[1],"%u",&input_pixelclock);
	}
	else
	{
		return error(ERROR, "Useage: pixelclock [new_pixelclock]");
	}

	if (input_pixelclock < min_clock || input_pixelclock > max_clock)
		return error(ERROR, "Pixelclock out of range!");

	if (set_pixelclock(input_pixelclock))
		return error(ERROR, "Error setting pixel clock");

	return NOERROR;

} /* call_set_pixelclock() */

/************************************************************************/
/* set_gain()	  			  		     		*/
/*									*/
/* Set the CMOS chip gain, between 0 and 100.				*/
/************************************************************************/

int usb_camera_set_gain(int new_gain)
{
	int errcode;
	
	if ( (errcode = is_SetHardwareGain(cam_pointer, new_gain, 
		IS_IGNORE_PARAMETER, IS_IGNORE_PARAMETER,IS_IGNORE_PARAMETER)) )
		return -1;

	usb_camera.gain = new_gain;

	return 0;	

} /* usb_camera_set_gain() */

/************************************************************************/
/* call_usb_camera_set_gain() 					     	*/
/*									*/
/* User Callable: Set the CMOS chip gain.				*/
/************************************************************************/

int cmd_camgain(int argc, char **argv)
{
	char s[80];
	unsigned int input_gain;

	if (argc > 1)
	{
		sscanf(argv[1],"%u",&input_gain);
	}
	else
	{
		return error(ERROR, "Useage: camgain [gain]");
	}
	if (usb_camera_set_gain(input_gain))
		return error(ERROR, "Failed to set gain!");

  	return NOERROR;

} /* call_usb_camera_set_gain() */

/************************************************************************/
/* toggle_destripe() 		 		    			*/
/*									*/
/* User Callable: toggle destriping the camera.				*/
/************************************************************************/

int cmd_destripe(int argc, char **argv)
{
	if (usb_camera.destripe)
	{
		usb_camera.destripe=FALSE;
		error(MESSAGE, "NOT destriping the raw images.");
	}
	else
	{
		usb_camera.destripe=TRUE;
		error(MESSAGE, "Destriping the raw images.");
	}
	return NOERROR;

} /* toggle_destripe() */

/************************************************************************/
/* create_dark() 		  		    			*/
/*									*/
/* Create a dark frame.				*/
/************************************************************************/

int create_dark(void)
{
	float *dark_increment;
	int i,j,k;

	dark_increment = malloc(cam_info.nMaxWidth*cam_info.nMaxHeight*sizeof(float));

	for (i=0;i<cam_info.nMaxWidth;i++)
	for (j=0;j<cam_info.nMaxHeight;j++) dark_increment[j*cam_info.nMaxWidth + i]=0.0;

	/* Lock the mutex - we don't want half a frame here. */

	pthread_mutex_lock(&usb_camera_mutex);

	/* Average the last frames */

	for (k=0;k<NUM_IMAGE_MEM;k++)
	{		
		for (j=0;j<cam_info.nMaxHeight;j++)
		for (i=0;i<cam_info.nMaxWidth;i++)
			dark_increment[j*cam_info.nMaxWidth + i] += data_frames[k][j*cam_info.nMaxWidth + i];
	}

	/* Now add this to the dark, which was previously subtracted. */

	for (j=0;j<cam_info.nMaxHeight;j++)
	for (i=0;i<cam_info.nMaxWidth;i++)
		dark[j*cam_info.nMaxWidth + i] += dark_increment[j*cam_info.nMaxWidth + i]/NUM_IMAGE_MEM;

	/* All done! */

	pthread_mutex_unlock(&usb_camera_mutex);
	free(dark_increment);

	return NOERROR;

} /* create_dark() */

/************************************************************************/
/* call_create_dark() 		 		    			*/
/*									*/
/* User Callable: create a dark frame.    				*/
/************************************************************************/

int cmd_dark(int argc, char **argv)
{
	create_dark();

	return NOERROR;

} /* call_create_dark() */

/************************************************************************/
/* zero_dark() 			  		    			*/
/*									*/
/************************************************************************/

int zero_dark(void)
{
	int	i,j;

	pthread_mutex_lock(&usb_camera_mutex);

	for (j=0;j<cam_info.nMaxHeight;j++) 
	for (i=0;i<cam_info.nMaxWidth;i++)
		dark[j*rectAOI.s32Width + i] = 0.0;

	pthread_mutex_unlock(&usb_camera_mutex);

	return NOERROR;

} /* zero_dark() */

/************************************************************************/
/* call_zero_dark() 		 		    			*/
/*									*/
/* User Callable: zero a dark frame.    				*/
/************************************************************************/

int cmd_zdark(int argc, char **argv)
{
	zero_dark();

	return NOERROR;

} /* call_zero_dark() */

/************************************************************************/
/* save_fits()								*/
/*									*/
/* Save an image in a fits file.					*/
/************************************************************************/

int cmd_save(int argc, char **argv)
{
	char	filename[256], filename_base[256], s[256];
	     int     year, month, day, doy;
	int	file_number = 0;
	FILE	*output;

	/* Is there an argument for the filename? */

	if (argc > 1)
	{
		if (strlen(argv[1]) == 0)
			return error(ERROR,"No valid filename.");

		strcpy(fits_filename, argv[1]);

	}
	else
	{
		/* We need to build the filename */

		/* Get current GMT */

//		get_ut_date(&year, &month, &day, &doy);

		/* Now we try and create a new filename */

		sprintf(filename_base,"test");
//"%s%4d_%02d_%02d_%s_",
//			get_data_directory(s), year,month,day,labao_name);

		for (file_number=1;file_number<=MAX_FILE_NUMBER;file_number++)
		{
			/* Create the filename */

			sprintf(filename,"%s%03d.fit",
				filename_base,file_number); 

			/* Does it already exist ? */

			if ((output = fopen(filename,"r")) == NULL) break;

			fclose(output);
		}

		if (file_number >= MAX_FILE_NUMBER)
		{
			return error(ERROR,
			"Exceeded maximum number of files with this name.");
		}

		strcpy(fits_filename, filename);
	}

	error(MESSAGE,"Saving image data in %s.", fits_filename);

	save_fits_file = TRUE;

	return NOERROR;

} /* save_fits() */

/************************************************************************/
/* save_fits_cube()							*/
/*									*/
/* Save multiple images in a fits file.					*/
/************************************************************************/

int cmd_savecube(int argc, char **argv)
{
	int 	n;
	char	s[567];

	if (!usb_camera_running) return error(ERROR,"Camera is not running.");

	/* Deal with the command lines */

	if (argc > 1)
	{
		sscanf(argv[1], "%d", &n);
	}


	if (n < 1) return error(ERROR,"Must have at least 1 frame.");

	/* We need to lock the mutex */

	pthread_mutex_lock(&usb_camera_mutex);

	/* Are we already doing this? */

	if (image_data_cube_num_frames > 0 &&
		image_data_cube_count_frames < image_data_cube_num_frames)
	{
		pthread_mutex_unlock(&usb_camera_mutex);
		return error(ERROR,"We seem to already be saving data.");
	}

	/* Allocate the memory we will need */

	image_data_cube = (float *)calloc((size_t)rectAOI.s32Height *
				(size_t)rectAOI.s32Width *(size_t)n,
				sizeof(float));

	if (image_data_cube == NULL)
	{
		pthread_mutex_unlock(&usb_camera_mutex);
		return error(ERROR,"Not enough memory - try fewer frames.");
	}

	/* OK, set things up so the frames will be saved */

	image_data_cube_pointer = image_data_cube;
	image_data_cube_num_frames = n;
	image_data_cube_count_frames = 0;

	/* OK, unlock things */

	pthread_mutex_unlock(&usb_camera_mutex);

	/* That should be all */

	error(MESSAGE, "Trying to save %d frames of data.", n);
	return NOERROR;

} /* save_fits_cube() */

/************************************************************************/
/* bgnd_complete_fits_cube()							*/
/*									*/
/* Wait and see if it is time to save a fits cube.			*/
/************************************************************************/

void bgnd_complete_fits_cube(void)
{
	char	filename[256], filename_base[256], s[256];
	int     year, month, day, doy;
	int	file_number = 0;
	FILE	*output;
	time_t	start;
	time_t	last;
	fitsfile *fptr;
	int	fits_status;
	long int naxis, naxes[3];
	int	bitpix;
	long int fpixel, nelements;
	int	i;
	char	s1[240], s2[240];

	/* Are we done??? */

	pthread_mutex_lock(&usb_camera_mutex);
	if (image_data_cube_num_frames == 0 ||
	    image_data_cube_count_frames < image_data_cube_num_frames)
	{
		pthread_mutex_unlock(&usb_camera_mutex);
		return;
	}
	pthread_mutex_unlock(&usb_camera_mutex);

	/* Get current GMT */

//	get_ut_date(&year, &month, &day, &doy);

	/* Now we try and create a new filename */

	sprintf(filename_base,"cube");
//"%s%4d_%02d_%02d_%s_wfs_",
//		get_data_directory(s), year,month,day,labao_name);

	for (file_number=1;file_number<=MAX_FILE_NUMBER;file_number++)
	{
		 /* Create the filename */

		 sprintf(filename,"%s%03d.fit",
			filename_base,file_number);

		 /* Does it already exist ? */

		 if ((output = fopen(filename,"r")) == NULL) break;
			 fclose(output);
	}

	if (file_number >= MAX_FILE_NUMBER)
	{
		 error(ERROR,
			"Exceeded maximum number of files with this name.");
		 return;
	}

	/* Setup for saving the fits file */

	naxis = 3;
	bitpix = FLOAT_IMG;
	naxes[0] = rectAOI.s32Width;
	naxes[1] = rectAOI.s32Height;
	naxes[2] = image_data_cube_num_frames;
	fpixel = 1;
	nelements = naxes[0] * naxes[1] * naxes[2];

	/* Create a new FITS file */

	fits_status = 0;
	if (fits_create_file(&fptr, filename, &fits_status))
	{
		error(ERROR,"Failed to create FITS file (%d).",
			fits_status);
	}

	/* Write required keywords into the header */

	if (fits_create_img(fptr, bitpix, naxis, naxes, &fits_status))
	{
		error(ERROR,"Failed to create FITS image (%d).",
		fits_status);
	}

	/* Write the FITS image */

	if (fits_write_img(fptr, TFLOAT, fpixel, nelements, 
		image_data_cube, &fits_status))
	{
		error(ERROR,"Failed to write FITS image (%d).",
			fits_status);
	}

	/* Now some header infromation */

	if(fits_update_key(fptr, TINT, "NUMFRAME", &image_data_cube_num_frames,
		"Number of frames", &fits_status))
	{
		error(ERROR,"Failed to write NUMFRAME (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "SENSORID", 
		&(cam_info.SensorID),
		"Sensor ID",&fits_status))
	{
		error(ERROR,"Failed to write SENSORID (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "MAXWIDTH", 
		&(cam_info.nMaxWidth),
		"Sensor Maximum width",&fits_status))
	{
		error(ERROR,"Failed to write MAXWIDTH (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "MAXHGHT", 
		&(cam_info.nMaxHeight),
		"Sensor Maximum height",&fits_status))
	{
		error(ERROR,"Failed to write MAXHGHT (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "AOI_X", 
		&(rectAOI.s32X),
		"AOI Position in X",&fits_status))
	{
		error(ERROR,"Failed to write AOI_X (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "AOI_Y", 
		&(rectAOI.s32Y),
		"AOI Position in Y",&fits_status))
	{
		error(ERROR,"Failed to write AOI_Y (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "AOI_DX", 
		&(rectAOI.s32Width),
		"AOI Position in DX",&fits_status))
	{
		error(ERROR,"Failed to write AOI_DX (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "AOI_DY", 
		&(rectAOI.s32Height),
		"AOI Position in DY",&fits_status))
	{
		error(ERROR,"Failed to write AOI_DY (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TFLOAT, "CAM_FPS",
		&usb_camera.fps,
		"Frames per second.",&fits_status))
	{
		error(ERROR,"Failed to write CAM_FPS (%d).",
			fits_status);
	}

	if(fits_update_key(fptr, TINT, "CAM_GAIN", 
		&usb_camera.gain,
		"Camera Gain",&fits_status))
	{
		error(ERROR,"Failed to write CAM_GAIN (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "CAM_CLK", 
		&usb_camera.pixelclock,
		"Camera pixel clock",&fits_status))
	{
		error(ERROR,"Failed to write CAM_CLK (%d).",
		fits_status);
	}

	if(fits_update_key(fptr, TINT, "LABSTART", &data_record_start,
                        "Time of first datum (mS)",&fits_status))
        {
                error(ERROR,"Failed to write LABSTART (%d).", fits_status);
        }

        if(fits_update_key(fptr, TINT, "LABSTOP", &data_record_stop,
                        "Time of last datum (mS)",&fits_status))
        {
                error(ERROR,"Failed to write LABSTOP (%d).", fits_status);
        }

	/* That should be enough! */

	if (fits_close_file(fptr, &fits_status))
	{
		error(ERROR,"Failed to close fits file (%d).",
			fits_status);
	}

	/* Clean up memory go */

	error(MESSAGE,  "Saved file %s", filename);

	pthread_mutex_lock(&usb_camera_mutex);
	image_data_cube_num_frames = 0;
        image_data_cube_count_frames = 0;
	free(image_data_cube);
	pthread_mutex_unlock(&usb_camera_mutex);

} /* complete_fits_cube() */

/************************************************************************/
/* usb_camera_set_exptime()		    				*/
/*									*/
/* Positive Number - Actual exposure time set				*/
/* -1 : Failed call.	   						*/
/************************************************************************/

double usb_camera_set_exptime(double exposure_in)
{
	double exposure;
	int errcode;

	exposure = exposure_in;
	if ((errcode = is_Exposure(cam_pointer, IS_EXPOSURE_CMD_SET_EXPOSURE,
		&exposure, sizeof(exposure))) )
	{
		if (errcode == IS_INVALID_PARAMETER)
			return -1.0; 
		else 
			return -2.0;
	}

	usb_camera.exptime = exposure_in;

	return exposure;

} /* set_frame_rate() */

/************************************************************************/
/* call_set_frame_rate()				    		*/
/*									*/
/* User Callable version of set_frame_rate  				*/
/************************************************************************/

int cmd_itime(int argc, char **argv)
{
	char s[100];
	double input_exptime, new_exptime;

	if (argc > 1)
	{
		sscanf(argv[1],"%lf",&input_exptime);
	}
	else
	{
		return error(MESSAGE, "Useage: itime [exposure time]");
	}

	if ((new_exptime = usb_camera_set_exptime(input_exptime)) < 0.0)
	{
		if (new_exptime == -1.0)
			return error(ERROR, "Invalid exposure time");
		else return error(ERROR, "Unknown error setting Frame Rate");
	}

	error(MESSAGE, "Exposure time now: %6.1lf", new_exptime);

	return NOERROR;
}


/************************************************************************/
/* usb_camera_is_running()						*/
/*									*/
/* So outside world can tell if teh camera is running or not.		*/
/************************************************************************/

bool usb_camera_is_running(void) {return usb_camera_running; }

/************************************************************************/
/* set_num_sum_frame()							*/
/*									*/
/* Get the USB camera area of interest 					*/
/************************************************************************/

int set_num_sum_frame(int num)
{
	if (num <= 0) return -1;

	num_sum_frame = num;
	count_sum_frame = 0;

	return num;

} /* set_num_sum_frame() */

/************************************************************************/
/* cmd_setnframe()						*/
/*									*/
/* User callable version.						*/
/************************************************************************/

int cmd_setnframe(int argc, char **argv)
{
	char	s[100];
	int	num;

	if (argc > 1)
	{
		sscanf(argv[1],"%d",&num);
	}

	if (set_num_sum_frame(num) < 0)
		return error(ERROR,"Invalid number of frames to sum");

	return NOERROR;

} /* call_set_num_sum_frame() */

/******************************************************************************/
/* cmd_image()                                                                */
/*                                                                            */
/* We've been asked for a new image. The last image number given should be    */
/* included. We return "image NUM LEN" with NUM the image number and LEN the  */
/* length of the zlib compressed image.                                       */
/******************************************************************************/   
#define IMAGE_BUFFER 65536
#define NUM_IMAGE_LEVELS 32
int cmd_image(int argc, char **argv)
{
	int client_last_frame=0, i, j, x, y, current_frame;
	uLongf len, clen;
	unsigned int outlen;
	char outstr[IMAGE_BUFFER], *compressed_image;
	float *data, *fp;
	float values[USB_DISP_X*USB_DISP_Y];
	float x_zero, y_zero;
	float last_fmax=-1e32, last_fmin=1e32, delta;
	if (client_socket==-1) return error(ERROR, "Command image only valid for non-text clients");
	if (argc >= 2){
		if (sscanf(argv[1], "%d", &client_last_frame)==0)
		 return error(ERROR, "Useage: image [NUM]");
		if (usb_camera_num_frames == client_last_frame){
		 sprintf(outstr, "image %d 0", client_last_frame);
		 write(client_socket, outstr, strlen(outstr));
		}	
	}
	/* Copy the image data */
	data = (float *)calloc((size_t)rectAOI.s32Height *
		(size_t)rectAOI.s32Width, sizeof(float));
	if (data == NULL) error(FATAL,"Not enough memory");
	pthread_mutex_lock(&usb_camera_mutex);	
	for(fp = data, j = 0; j < rectAOI.s32Height; j++)
	for(i = 0; i < rectAOI.s32Width; i++){ ;
		*fp = data_frames[current_data_frame_ix][j*rectAOI.s32Width + i];
		if (*fp > last_fmax) last_fmax=*fp;
		if (*fp < last_fmin) last_fmin=*fp;
		fp++;
	}
	current_frame = usb_camera_num_frames;
	pthread_mutex_unlock(&usb_camera_mutex);

	/* How do we translate from the image to our array? */

	if (USB_DISP_X == rectAOI.s32Width)
	{
		usb_camera.x_mult = 1.0;
		x_zero = 0.0;
	}
	else
	{
		usb_camera.x_mult = 
			(float)(rectAOI.s32Width)/(float)(USB_DISP_X);
		x_zero = 1.0 - usb_camera.x_mult * 1.0;
	}

	if (USB_DISP_Y == rectAOI.s32Height)
	{
		usb_camera.y_mult = 1.0;
		y_zero = 0.0;
	}
	else
	{
		usb_camera.y_mult = 
			(float)(rectAOI.s32Height)/(float)(USB_DISP_Y);
		y_zero = 1.0 - usb_camera.y_mult * 1.0;
	}

	/* Now make a small version of the image */
	delta = (last_fmax - last_fmin)/NUM_IMAGE_LEVELS;
	for(j = 0; j < USB_DISP_Y; j++)
	for(i = 0; i < USB_DISP_X; i++)
	{
		x = (int)(usb_camera.x_mult * i + x_zero + 0.5);
		if (x < 0)
			x = 0;
		else if (x >= rectAOI.s32Width)
			x = rectAOI.s32Width-1;

		y = (int)(usb_camera.y_mult * j + y_zero + 0.5);
		if (y < 0)
			y = 0;
		else if (y >= rectAOI.s32Height)
			y = rectAOI.s32Height-1;
		/* Copy this accross, with a finite number of image levels for display purposes */
		values[j*USB_DISP_X + i] = delta * (int)(data[y*rectAOI.s32Width + x] /delta) ;
	}
	/* Compress the image */
	len = USB_DISP_X * USB_DISP_Y * sizeof(float);
	clen = len;

        if ((compressed_image = malloc(clen))==NULL)
		error(FATAL, "Out of memory");

	if ((i = compress((unsigned char *)compressed_image,
                &clen,
                (unsigned char *)values, len)) < Z_OK)
        {
             return error(ERROR,
		"Failed to compress image. %d",i);
        }
	sprintf(outstr, "image %d %d ", current_frame, (int)clen);
	outlen = clen + strlen(outstr);
	if (outlen > IMAGE_BUFFER) return error(ERROR, "Compressed image too large!");
	memcpy(outstr + strlen(outstr), compressed_image, clen);
	write(client_socket, outstr, outlen);

	return NOERROR;
}

/* At the moment, this just saves the next image as a fits file if we've been asked
to do so. Merge with cmd_save? */
void bgnd_usb_camera(void)
{
/*	time_t dt;
	static float	**values = NULL;
	static float    **data = NULL;
	char	*picture;
	int	i, j, x, y;
	float	x_zero, y_zero;
	

	
	struct smessage usbmess;
	struct smessage cenmess;
	struct smessage imagemess;
	float  *cen_data, *compressed_cen_data;
	float  *image, *compressed_image;
	uLongf	len, clen; */

	int i,j;
	/* Static variables */
	static int	last_num_frames = 0;
	/* FITS related variables*/
	fitsfile *fptr;
	int	fits_status;
	long int naxis, naxes[2];
	float	*data_cube, *fp;
	int	bitpix;
	long int fpixel, nelements;

	/* Do nothing if we don't have a new image*/

	if (usb_camera_num_frames == last_num_frames) return;
	last_num_frames = usb_camera_num_frames;

	

	/* I guess this is the point to fill up the status variables etc 
	   (min, max, mean). Or doesn't that matter as it is command/response ??? */
		
	/* Are we saving a fits file? */

	if (save_fits_file)
	{
		/* Build the data image */
		data_cube = (float *)calloc((size_t)rectAOI.s32Height *
			(size_t)rectAOI.s32Width, sizeof(float));
		if (data_cube == NULL) error(FATAL,"Not enough memory");

		/* Copy the image data accross */
		pthread_mutex_lock(&usb_camera_mutex);	
		for(fp = data_cube, j = 0; j < rectAOI.s32Height; j++)
		for(i = 0; i < rectAOI.s32Width; i++)
			*fp++ = data_frames[current_data_frame_ix][j*rectAOI.s32Width + i];
		pthread_mutex_unlock(&usb_camera_mutex);

		/* Setup for saving the fits file */

		naxis = 2;
		bitpix = FLOAT_IMG;
		naxes[0] = rectAOI.s32Width;
		naxes[1] = rectAOI.s32Height;
		fpixel = 1;
		nelements = naxes[0] * naxes[1];

		/* Create a new FITS file */

		fits_status = 0;
		if (fits_create_file(&fptr,fits_filename,&fits_status))
		{
			error(ERROR,"Failed to create FITS file (%d).",
				fits_status);
		}

		/* Write required keywords into the header */

		if (fits_create_img(fptr, bitpix, naxis, naxes, 
			&fits_status))
		{
			error(ERROR,"Failed to create FITS image (%d).",
			     fits_status);
		}

		/* Write the FITS image */

		if (fits_write_img(fptr, TFLOAT, fpixel, nelements, 
			data_cube, &fits_status))
		{
			error(ERROR,"Failed to write FITS image (%d).",
				fits_status);
		}
	    

		/* Now some header infromation */

		if(fits_update_key(fptr, TINT, "SENSORID", 
			&(cam_info.SensorID), "Sensor ID",&fits_status))
		{
			error(ERROR,"Failed to write SENSORID (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "MAXWIDTH", 
			&(cam_info.nMaxWidth),
			"Sensor Maximum width",&fits_status))
		{
			error(ERROR,"Failed to write MAXWIDTH (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "MAXHGHT", 
			&(cam_info.nMaxHeight),
			"Sensor Maximum height",&fits_status))
		{
			error(ERROR,"Failed to write MAXHGHT (%d).",
		     	fits_status);
		}

		if(fits_update_key(fptr, TINT, "AOI_X", 
			&(rectAOI.s32X),
			"AOI Positionin X",&fits_status))
		{
			error(ERROR,"Failed to write AOI_X (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "AOI_Y", 
			&(rectAOI.s32Y),
			"AOI Positionin Y",&fits_status))
		{
			error(ERROR,"Failed to write AOI_Y (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "AOI_DX", 
			&(rectAOI.s32Width),
			"AOI Positionin DX",&fits_status))
		{
			error(ERROR,"Failed to write AOI_DX (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "AOI_DY", 
			&(rectAOI.s32Height),
			"AOI Positionin DY",&fits_status))
		{
			error(ERROR,"Failed to write AOI_DY (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TFLOAT, "CAM_FPS",
			&usb_camera.fps,
			"Frames per second.",&fits_status))
		{
			error(ERROR,"Failed to write CAM_FPS (%d).",
				fits_status);
		}

		if(fits_update_key(fptr, TINT, "CAM_GAIN", 
			&usb_camera.gain, "Camera Gain",&fits_status))
		{
			error(ERROR,"Failed to write CAM_GAIN (%d).",
			fits_status);
		}

		if(fits_update_key(fptr, TINT, "CAM_CLK", 
			&usb_camera.pixelclock,
			"Camera pixel cloxk",&fits_status))
		{
			error(ERROR,"Failed to write CAM_CLK (%d).",
			fits_status);
		}

		/* That should be enough! */

		if (fits_close_file(fptr, &fits_status))
		{
			error(ERROR,"Failed to close fits file (%d).",
				fits_status);
		}

		/* That is all */

		save_fits_file = FALSE;
		free(data_cube);
	}


	return;
}
