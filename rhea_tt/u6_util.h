#include "u6.h"

struct s_U6_state {
    char FIOs[8];
    char EIOs[8];
    char CIOs[4];
    double DAC0;
    double DAC1;
    double AINs[14];
    int Counters[2];
    int Timers[4];
};

extern struct s_U6_state U6_state;

int cmd_fio(int argc, char **argv);
int cmd_eio(int argc, char **argv);
int cmd_cio(int argc, char **argv);
int cmd_dacs(int argc, char **argv);
int cmd_get_ains(int argc, char **argv);
int cmd_get_timers(int argc, char **argv);
int cmd_get_counters(int argc, char **argv);

int open_U6(void);
int close_U6(void);
int quadrature_U6(void);
int configIO_U6(uint8 numTimers, uint8 counterEnable, uint8 pinOffset);
int u6_send_port_state(uint8 FIO_mask, uint8 EIO_mask, uint8 CIO_mask, uint8 FIO_dir, uint8 EIO_dir, uint8 CIO_dir);
int u6_all_out(void);
int u6_all_in(void);
int all_ain(void);
