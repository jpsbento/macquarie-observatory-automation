/************************************************************************/
/* uicoms.h								*/
/*                                                                      */
/* General Header File.							*/
/************************************************************************/
/*                                                                      */
/* Author : Tony Johnson & Theo ten Brummelaar                          */
/* Date   : Original Version 1990 - ported to Linux 1998                */
/*          Hacked by MJI 2015 						*/
/************************************************************************/

#ifndef __UICOMS__
#define __UICOMS__

/*
 * General include files 
 */

#include <stdio.h>
//#include <curses.h>
#include <stdbool.h>
#include <time.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdarg.h>
#include <ctype.h>

#define BUFFER_SIZE     1024		/* For serial read/writes */

/*
 * Constants
 */

#define MAXLEVEL	20	/* Maximum menu level */
#define MAXSTRING	41	/* Maximum string length for prompts and names*/
#define MAXENTRY	10	/* Maximum number of entries in a menu */
#define MAXMENUS	100	/* Maximum number of menus */
#define MAXAUTO		100	/* Maximum number of ftns in auto list */
#define MAXSCRIPT	100	/* Maximum number of lines in script */

/* Check whgat these are.... do we use them at all or are they roberts? */

#define MAXFIELDS (MAIN_LINES-4)
#define MAXPAGES	50
#define MAX_WAIT_TIME	5
#define MAX_ATTEMPTS	2

/*
 * The constants above are the initial values for the global variables below.
 */

#define YES		1
#define NO		0
#ifndef TRUE
#define TRUE		1
#define FALSE		0
#endif
#define OFF		0
#define ON		1
#define EVEN		2
#define ODD		3

#define LOCK_DIR	"/var/lock"
#define LOCK_START	"LCK.."


/*
 * Macro functions
 */

/*
 * Name changed from clear_screen to ui_clear_screen to avoid
 * conflict with /usr/5include/term.h
 */

/* #define kbhit()			char_waiting(fileno(stdin)) */

#define serial_char_waiting(port) char_waiting(port.fd)

#define serial_putstr(port,s)	write(port.fd,s,strlen(s))

#define ui_clear_screen()	system("clear")

#define menu_alloc()	(struct smenu *)malloc(sizeof(struct smenu))
#define list_alloc()	(struct slist *)malloc(sizeof(struct slist))

#define	working()	werase(system_ol_window); \
			mvwaddstr(system_ol_window,0,0,"Working. . ."); \
			touchwin(system_ol_window); \
			wrefresh(system_ol_window)

#define not_working()	touchwin(system_window);wrefresh(system_window)

#define clean_command_line()	wmove(command_window,0,2); \
				wclrtoeol(command_window); \
				wrefresh(command_window)

#define fill(x) 	for(i=0; i<BOX_WIDTH-2; i++) putchar(x)
#define blank_line()	putchar(CHAR_VERT); fill(' '); putchar(CHAR_VERT); \
			putchar('\n')

#define no_socket()	if (active_socket != -1)\
			{\
			   return error(ERROR,\
				"Command %s not allowed via socket.\n"\
				,argv[0]);\
			}

#define socket_test_args(num,use) if(active_socket != -1 && argc-1 != num)\
			{\
			    return error(ERROR,"usage: %s %s\n",argv[0],use);\
			}
					
#define close_connect_socket(fd) close(fd)



struct sserial 
{
	int    fd;		     /* Port file descriptor */
	char   name[81];	     /* Port name */
	char   lock_file[81];	     /* lock_file name */
        struct termios orig_termios; /* original termio data */
        struct termios curr_termios; /* current termio data */
};


/*
 * The following structure is for circular buffers 
 */

typedef	struct sbuffer{
			unsigned char	*bottom;
			unsigned char	*top;
			unsigned char 	*in;
			unsigned char	*out;

		} BUFFER;

extern int client_socket;

/* 
 * These macros let you play with buffers
 */

#define	buffer_not_full(x)	(x->in != x->out)
#define buffer_full(x)		(x->in == x->out)
#define buffer_not_empty(x)	((x->out != x->in - 1) && \
				((x->out != x->top) || (x->in != x->bottom)))
#define buffer_empty(x)		((x->out == x->in - 1) || \
				((x->out == x->top) && (x->in == x->bottom)))

#define buffer_in(x,y)		{if (buffer_not_full(x)) \
					 {\
						*(x->in) = (y);\
						if (++(x->in) > x->top) \
							x->in = x->bottom;\
					 }\
				}
	
#define buffer_out(x,y)		{if (buffer_not_empty(x)) \
					 {\
						if (++(x->out) > x->top) \
							x->out = x->bottom;\
						(y) = *(x->out);\
					 }\
				}


/* 
 * Error messages
 */

#ifndef _ERRDEFS_
#define _ERRDEFS_

#define MESSAGE 1 /* Use error system for putting up a message */
#define NOERROR	0 /* No error has occured */
#define WARNING (-1) /* A warning, nothing too dangerous has happened */
#define ERROR	(-2) /* Some kind of major error.Prog does not have to reboot */
#define FATAL	(-3) /* A fatal error has occured. The programme must exit(1)*/ 
#endif

#define COMMAND_BUFFERSIZE 65536
#define MAX_COMMAND_SIZE 80

/*
 * Prototypes
 */

/* uicoms.c */

extern int error(int level, char *the_string, ...);
int open_server_socket(void);
void close_server_socket(void);
int get_next_command(char *command);
extern struct sserial open_serial_port(char *port_name, bool blocking);
extern char 	*lock_file_name(char *port, char *s);
extern int	close_serial_port(struct sserial port);
extern int set_serial_baud_rate(struct sserial *port, speed_t speed);
extern int set_serial_parity(struct sserial *port, int parity);
extern int set_serial_xonxoff(struct sserial *port, int xonxoff);
extern int set_serial_hard_handshake(struct sserial *port, int hard_handshake);
extern int set_serial_bitlength(struct sserial *port, int bits);
extern int set_serial_stopbits(struct sserial *port, int bits);
extern unsigned char serial_getchar(struct sserial port);
extern unsigned char serial_putchar(struct sserial port, unsigned char c);
extern int serial_print(struct sserial port, char *fmt, ...);
extern int serial_scan(struct sserial port, char *fmt, ...);
extern char *serial_gets(struct sserial port, char *s, int n);

#endif
