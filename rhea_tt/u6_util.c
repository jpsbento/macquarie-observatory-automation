//Author : LabJack
//April 5, 2011
//This example demonstrates how to write and read some or all analog I/O.
//By default, it records the time for 1000 iterations and divides by 1000,
//to allow measurement of the basic command/response communication times.  These
//times should be comparable to the Windows command/response communication
//times documented in Section 3.1 of the U6 User's Guide.

#include <stdlib.h>
#include "u6_util.h"
#include "uicoms.h"

const uint8 numChannels = 4; //Number of AIN channels, 0-14.  .
const uint8 settlingFactor = 0; //0=5us, 1=10us, 2=100us, 3=1ms, 4=10ms.  Default 0.
const uint8 gainIndex = 0; //0 = +-10V, 1 = +-1V, 2 = +-100mV, 3 = +-10mV, 15=autorange.  Default 0.
const uint8 resolution = 8; //1=default, 1-8 for high-speed ADC, 9-13 for high-res ADC on U6-Pro. Default 1.
const uint8 differential = 0; //Indicates whether to do differential readings.  Default 0 (false).

static u6CalibrationInfo calInfo;
static HANDLE hDevice;
static bool is_U6_open=FALSE;
static bool asked_for_all=FALSE;


/* Globals */

struct s_U6_state U6_state;

static int current_AIN=0;

int cmd_fio(int argc, char **argv)
{
	char s[100];
	unsigned int output, value;
	if (argc > 2)
	{
		if (sscanf(argv[1],"%u",&output) != 1)
            return error(ERROR, "Error parsing input");
        if (sscanf(argv[2],"%u",&value) != 1)
            return error(ERROR, "Error parsing input");	}
	else
	{
		return error(ERROR, "Useage: fio [pin] [0|1]");
	}
    /* Some error checking */
    if (output > 7) return error(ERROR, "Only outputs 0-7 valid");
    if (value > 1) return error(ERROR, "Only digital outputs 0 or 1");
    /* Set the state and wait for the background task to change it. */
    U6_state.FIOs[output]=value;

	return NOERROR;
}

int cmd_eio(int argc, char **argv)
{
	char s[100];
	unsigned int output, value;
	if (argc > 2)
	{
		if (sscanf(argv[1],"%u",&output) != 1)
            return error(ERROR, "Error parsing input");
        if (sscanf(argv[2],"%u",&value) != 1)
            return error(ERROR, "Error parsing input");	}
	else
	{
		return error(ERROR, "Useage: eio [pin] [0|1]");
	}
    /* Some error checking */
    if (output > 7) return error(ERROR, "Only outputs 0-7 valid");
    if (value > 1) return error(ERROR, "Only digital outputs 0 or 1");
    /* Set the state and wait for the background task to change it. */
    U6_state.EIOs[output]=value;

	return NOERROR;
}

int cmd_cio(int argc, char **argv)
{
	char s[100];
	unsigned int output, value;
	if (argc > 2)
	{
		if (sscanf(argv[1],"%u",&output) != 1)
            return error(ERROR, "Error parsing input");
        if (sscanf(argv[2],"%u",&value) != 1)
            return error(ERROR, "Error parsing input");
	}
	else
	{
		return error(ERROR, "Useage: cio [pin] [0|1]");
	}
    /* Some error checking */
    if (output > 3) return error(ERROR, "Only outputs 0-3 valid");
    if (value > 1) return error(ERROR, "Only digital outputs 0 or 1");
    /* Set the state and wait for the background task to change it. */
    U6_state.CIOs[output]=value;

	return NOERROR;
}

int cmd_dacs(int argc, char **argv)
{
    char s[100];
	double dac0, dac1;
	if (argc > 2)
	{
		if (sscanf(argv[1],"%lf",&dac0) != 1)
            return error(ERROR, "Error parsing input");
		if (sscanf(argv[2],"%lf",&dac1) != 1)
            return error(ERROR, "Error parsing input");
	}
	else
	{
		return error(ERROR, "Useage: dacs [DAC0 (V)] [DAC1 (V)]");
	}
    /* Some error checking */
    if (dac0<0 || dac1<0) return error(ERROR, "Voltage must be greater than 0V");
    if (dac0>5 || dac1>5) return error(ERROR, "Voltage must be less than 5V");
    /* Set the state and wait for the background task to change it. */
    U6_state.DAC0=dac0;
    U6_state.DAC1=dac1;
    return NOERROR;
}

/* Get the first 4 analogue input values.*/
int cmd_get_ains(int argc, char **argv)
{
    return error(MESSAGE, "%lf9.6 %lf9.6 %lf9.6 %lf9.6", 
        U6_state.AINs[0],U6_state.AINs[1],U6_state.AINs[2],U6_state.AINs[3]);
}

int cmd_get_timers(int argc, char **argv)
{
    return error(MESSAGE, "%d %d %d %d", 
        U6_state.Timers[0],U6_state.Timers[1],U6_state.Timers[2],U6_state.Timers[3]);
}

int cmd_get_counters(int argc, char **argv)
{
    return error(MESSAGE, "%d %d", 
        U6_state.Counters[0],U6_state.Counters[1]);
}

int open_U6()
{
    int i;
    //Opening first found U6 over USB
    if( (hDevice = openUSBConnection(-1)) == NULL )
    {
        is_U6_open=FALSE;
        return error(ERROR, "Could not open U6.");
    }

    //Getting calibration information from U6
    if( getCalibrationInfo(hDevice, &calInfo) < 0 )
    {
        closeUSBConnection(hDevice);
        is_U6_open=FALSE;
        return error(ERROR, "Could not get calibration info for U6");
    }
    for (i=0;i<2;i++){
        U6_state.Counters[i]=0;
    }
    for (i=0;i<4;i++){
        U6_state.CIOs[i]=0;
        U6_state.Timers[i]=0;
    }
    for (i=0;i<8;i++){
        U6_state.FIOs[i]=0;
        U6_state.EIOs[i]=0;
    }
    for (i=0;i<14;i++){
        U6_state.AINs[i]=0.0;
    }    
    U6_state.DAC0=2.5;
    U6_state.DAC1=2.5;
    is_U6_open=TRUE;
    return 0;
}

/* Set timer0 and timer1 to quadrature and reset the counter. */
int quadrature_U6(void)
{
    char sendBuff[12];
    int i, sendChars;

    if (!is_U6_open) return NOERROR;
 
   sendBuff[1] = (uint8)(0xF8);  //Command byte
    sendBuff[2] = 3;              //Number of data words (.5 word for echo, 2.5
                                  //words for IOTypes and data)
    sendBuff[3] = (uint8)(0x00);  //Extended command number

    sendBuff[6] = 0;    //Echo
    sendBuff[7] = 43;   //IOType is Timer#Config
    sendBuff[8] = 0x08;    //Quadrature
    sendBuff[9] = 0x00;    //Writemask (for EIO)
    sendBuff[10] = 0x00;   //Writemask (for CIO)
    sendBuff[11] = 0x00;   //dummy    
    extendedChecksum(sendBuff, 12);

    //Sending command to U6
    if( (sendChars = LJUSB_Write(hDevice, sendBuff, 12)) < 12 )
    {
        if(sendChars == 0)
            return error(ERROR, "Feedback (all) error : write failed\n");
        else
            return error(ERROR,"Feedback (all) error : did not write all of the buffer\n");        
    }

    // Now for the 2nd timer...
    sendBuff[7] = 45;   //IOType is Timer#Config 
    extendedChecksum(sendBuff,12);

     //Sending command to U6
    if( (sendChars = LJUSB_Write(hDevice, sendBuff, 12)) < 12 )
    {
        if(sendChars == 0)
            return error(ERROR, "Feedback (all) error : write failed\n");
        else
            return error(ERROR,"Feedback (all) error : did not write all of the buffer\n");
    }

    return NOERROR;
}

/* configIO_U6(2,1,8) */
int configIO_U6(uint8 numTimers, uint8 counterEnable, uint8 pinOffset)
{ 
    uint8 sendBuff[16], recBuff[16];
    uint16 checksumTotal;
    int sendChars, recChars, i;

    if (!is_U6_open) return NOERROR;

    sendBuff[1] = (uint8)(0xF8);  //Command byte
    sendBuff[2] = (uint8)(0x05);  //Number of data words
    sendBuff[3] = (uint8)(0x0B);  //Extended command number

    sendBuff[6] = 1;  //Writemask : Setting writemask for timerCounterConfig (bit 0)

    sendBuff[7] = numTimers;      //NumberTimersEnabled
    sendBuff[8] = counterEnable;  //CounterEnable: Bit 0 is Counter 0, Bit 1 is Counter 1
    sendBuff[9] = pinOffset;  //TimerCounterPinOffset:  Setting to 1 so Timer/Counters start on FIO1

    for( i = 10; i < 16; i++ )
        sendBuff[i] = 0;  //Reserved
    extendedChecksum(sendBuff, 16);

    //Sending command to U6
    if( (sendChars = LJUSB_Write(hDevice, sendBuff, 16)) < 16 )
    {
        if(sendChars == 0)
            printf("ConfigIO error : write failed\n");
        else
            printf("ConfigIO error : did not write all of the buffer\n");
        return -1;
    }

    //Reading response from U6
    if( (recChars = LJUSB_Read(hDevice, recBuff, 16)) < 16 )
    {
        if(recChars == 0)
            printf("ConfigIO error : read failed\n");
        else
            printf("ConfigIO error : did not read all of the buffer\n");
        return -1;
    }

    checksumTotal = extendedChecksum16(recBuff, 16);
    if( (uint8)((checksumTotal / 256 ) & 0xff) != recBuff[5] )
    {
        printf("ConfigIO error : read buffer has bad checksum16(MSB)\n");
        return -1;
    }

    if( (uint8)(checksumTotal & 0xff) != recBuff[4] )
    {
        printf("ConfigIO error : read buffer has bad checksum16(LBS)\n");
        return -1;
    }

    if( extendedChecksum8(recBuff) != recBuff[0] )
    {
        printf("ConfigIO error : read buffer has bad checksum8\n");
        return -1;
    }

    if( recBuff[1] != (uint8)(0xF8) || recBuff[2] != (uint8)(0x05) || recBuff[3] != (uint8)(0x0B) )
    {
        printf("ConfigIO error : read buffer has wrong command bytes\n");
        return -1;
    }

    if( recBuff[6] != 0 )
    {
        printf("ConfigIO error : read buffer received errorcode %d\n", recBuff[6]);
        return -1;
    }

    return 0;
}



int close_U6()
{
    is_U6_open=FALSE;
    closeUSBConnection(hDevice);
}

//Calls the Feedback low-level command numIterations times and calculates the
//time per iteration.
int u6_send_port_state(uint8 FIO_mask, uint8 EIO_mask, uint8 CIO_mask, uint8 FIO_dir, uint8 EIO_dir, uint8 CIO_dir)
{
    uint8 *sendBuff, *recBuff;
    uint16 checksumTotal;
    uint32 bits32;

    int sendChars, recChars, i, j, sendSize, recSize;
    int ret = 0;

    if (!is_U6_open) return error(ERROR, "U6 is not yet open - can't set port state");

    //Setting up a Feedback command that will set CIO0-3 as input, and
    //set DAC0 voltage
    sendBuff = (uint8 *)malloc(14*sizeof(uint8));  //Creating an array of size 14
    recBuff = (uint8 *)malloc(10*sizeof(uint8));   //Creating an array of size 10

    sendBuff[1] = (uint8)(0xF8);  //Command byte
    sendBuff[2] = 4;              //Number of data words (.5 word for echo, 3.5
                                  //words for IOTypes and data)
    sendBuff[3] = (uint8)(0x00);  //Extended command number

    sendBuff[6] = 0;    //Echo
    sendBuff[7] = 29;   //IOType is PortDirWrite
    sendBuff[8] = FIO_mask;    //Writemask (for FIO)
    sendBuff[9] = EIO_mask;    //Writemask (for EIO)
    sendBuff[10] = CIO_mask;   //Writemask (for CIO)
    sendBuff[11] = FIO_dir;    //Direction (for FIO)
    sendBuff[12] = EIO_dir;    //Direction (for EIO)
    sendBuff[13] = CIO_dir;    //Direction (for CIO)

    extendedChecksum(sendBuff, 14);

    //Sending command to U6
    if( (sendChars = LJUSB_Write(hDevice, sendBuff, 14)) < 14 )
    {
        if(sendChars == 0)
            printf("Feedback (CIO input) error : write failed\n");
        else
            printf("Feedback (CIO input) error : did not write all of the buffer\n");
        ret = -1;
        goto cleanmem;
    }

    //Reading response from U6
    if( (recChars = LJUSB_Read(hDevice, recBuff, 10)) < 10 )
    {
        if( recChars == 0 )
        {
            printf("Feedback (CIO input) error : read failed\n");
            ret = -1;
            goto cleanmem;
        }
        else
            printf("Feedback (CIO input) error : did not read all of the buffer\n");
    }

    checksumTotal = extendedChecksum16(recBuff, 10);
    if( (uint8)((checksumTotal / 256) & 0xff) != recBuff[5] )
    {
        printf("Feedback (CIO input) error : read buffer has bad checksum16(MSB)\n");
        ret = -1;
        goto cleanmem;
    }

    if( (uint8)(checksumTotal & 0xff) != recBuff[4] )
    {
        printf("Feedback (CIO input) error : read buffer has bad checksum16(LBS)\n");
        ret = -1;
        goto cleanmem;
    }

    if( extendedChecksum8(recBuff) != recBuff[0] )
    {
        printf("Feedback (CIO input) error : read buffer has bad checksum8\n");
        ret = -1;
        goto cleanmem;
    }

    if( recBuff[1] != (uint8)(0xF8) || recBuff[3] != (uint8)(0x00) )
    {
        printf("Feedback (CIO input) error : read buffer has wrong command bytes \n");
        ret = -1;
        goto cleanmem;
    }

    if( recBuff[6] != 0 )
    {
        printf("Feedback (CIO input) error : received errorcode %d for frame %d in Feedback response. \n", recBuff[6], recBuff[7]);
        ret = -1;
        goto cleanmem;
    }

cleanmem:
    free(sendBuff);
    free(recBuff);
}

/* In the camera thread, the procedure should be:

camera frame
calculations
input from last USB (quick)
output to USB 

This enables the longest possible wait for USB input, e.g. for AIN settling. */

#define ALL_IN_NBYTES 20
int u6_all_in()
{
    uint16 checksumTotal;
	uint32 bits32;
	int retInt; 
    int recChars, recSize;
    uint8 recBuff[ALL_IN_NBYTES];

    if (!is_U6_open) return NOERROR;
    /* We can only get an input if we've asked for one. */
    if (!asked_for_all) return NOERROR;
    asked_for_all=FALSE;
    //Reading response from U6
    if( (recChars = LJUSB_Read(hDevice, recBuff, ALL_IN_NBYTES)) < ALL_IN_NBYTES )
    {
//        is_U6_open=FALSE; /* !!! Think about this !!! */
        
        if( recChars == 0 )
        {
            return error(ERROR, "Feedback (all) error : read failed");
        }
        else
            return error(ERROR, "Feedback (all) error : did not read all of the buffer");
    }

    checksumTotal = extendedChecksum16(recBuff, ALL_IN_NBYTES);

    if( (uint8)((checksumTotal / 256) & 0xff) != recBuff[5] )
    {
        return error(ERROR,"Feedback (all) error : read buffer has bad checksum16(MSB)");
    }

    if( (uint8)(checksumTotal & 0xff) != recBuff[4] )
    {
        return error(ERROR, "Feedback (all) error : read buffer has bad checksum16(LBS)");
    }

    if( extendedChecksum8(recBuff) != recBuff[0] )
    {
        is_U6_open=FALSE;
        error(ERROR,"Feedback (all) error : read buffer has bad checksum8");
    }

    if( recBuff[1] != (uint8)(0xF8) || recBuff[3] != (uint8)(0x00) )
    {
        error(ERROR, "Feedback (all) error : read buffer has wrong command bytes %u %u", recBuff[1], recBuff[3]);
    }

    if( recBuff[6] != 0 )
    {
        error(ERROR,"Feedback (all) error : received errorcode %u for frame %u in Feedback response. \n", recBuff[6], recBuff[7]);
    }

    bits32 = recBuff[9] + recBuff[10]*256 + recBuff[11]*65536;
	getAinVoltCalibrated(&calInfo, resolution, gainIndex, 1, bits32, &(U6_state.AINs[current_AIN]) );
    // Counter 0
    U6_state.Counters[0] = recBuff[12] + (1<<8)*recBuff[13] + (1<<16)*recBuff[14] + (1<<24)*(char)recBuff[15];
    // Timer 0. As output is signed, we have to cast to a char.
    U6_state.Timers[0] = recBuff[16] + (1<<8)*recBuff[17] + (1<<16)*recBuff[18] + (1<<24)*(char)recBuff[19];
    
    return NOERROR;
}

#define ALL_OUT_NBYTES 30
int u6_all_out()
{
    uint16 checksumTotal, bits16;
    uint8 FIO_state=0, EIO_state=0, CIO_state=0;
    char sendBuff[ALL_OUT_NBYTES];
    int i, sendChars;
    if (!is_U6_open) return NOERROR;
    /* If we've already sent the command with no response, do nothing. */
    if (asked_for_all) return NOERROR;

    for (i=7;i>=0;i--){
        FIO_state<<=1;
        if ( U6_state.FIOs[i]) FIO_state++;
    }
    for (i=7;i>=0;i--){
        EIO_state<<=1;
        if ( U6_state.EIOs[i]) EIO_state++;
    }
    for (i=3;i>=0;i--){
        CIO_state<<=1;
        if ( U6_state.CIOs[i]) CIO_state++;
    }
    current_AIN++;
    if (current_AIN == numChannels) current_AIN=0;

    sendBuff[1] = (uint8)(0xF8);  //Command byte
    sendBuff[2] = 12;              //Number of data words (.5 word for echo, 11.5
                                  //words for IOTypes and data)
    sendBuff[3] = (uint8)(0x00);  //Extended command number

    sendBuff[6] = 0;    //Echo
    sendBuff[7] = 27;   //IOType is PortStateWrite
    sendBuff[8] = 0xff;    //Writemask (for FIO)
    sendBuff[9] = 0xff;    //Writemask (for EIO)
    sendBuff[10] = 0xf;   //Writemask (for CIO)
    sendBuff[11] = FIO_state;    //Direction (for FIO)
    sendBuff[12] = EIO_state;    //Direction (for EIO)
    sendBuff[13] = CIO_state;    //Direction (for CIO)
    
    //Setting DAC0 
    sendBuff[14] = 38;    //IOType is DAC0(16-bit)
	
    //Convert value
    getDacBinVoltCalibrated16Bit(&calInfo, 0, U6_state.DAC0, &bits16);
    sendBuff[15] = (uint8)(bits16&255);
    sendBuff[16] = (uint8)(bits16/256);

    //Convert value
    sendBuff[17] = 39;    //IOType is DAC1(16-bit)
	
    //Value is 2.5 volts (in binary)
    getDacBinVoltCalibrated16Bit(&calInfo, 0, U6_state.DAC1, &bits16);
    sendBuff[18] = (uint8)(bits16&255);
    sendBuff[19] = (uint8)(bits16/256);
 
    //Request an AIN
 	sendBuff[20] = 2;     //IOType is AIN24

	//Positive Channel (bits 0 - 4), LongSettling (bit 6) and QuickSample (bit 7)
	sendBuff[21] = current_AIN; //Positive Channel
	sendBuff[22] = (uint8)(resolution&15) + (uint8)((gainIndex&15)*16);   //ResolutionIndex(Bits 0-3), GainIndex(Bits 4-7)
	sendBuff[23] = (uint8)(settlingFactor&7);  //SettlingFactor(Bits 0-2)

    //Request Counter 0
    sendBuff[24] = 54;     //IOType is Timer#
    sendBuff[25] = 0; //Don't reset
    //Request Timer 0
    sendBuff[26] = 42;     //IOType is Timer#
    sendBuff[27] = 0;    //Don't reset.
    sendBuff[28] = 0;
    sendBuff[29] = 0;
    
    extendedChecksum(sendBuff, ALL_OUT_NBYTES);

    //Sending command to U6
    if( (sendChars = LJUSB_Write(hDevice, sendBuff, ALL_OUT_NBYTES)) < ALL_OUT_NBYTES )
    {
        if(sendChars == 0)
            return error(ERROR, "Feedback (all) error : write failed\n");
        else
            return error(ERROR,"Feedback (all) error : did not write all of the buffer\n");        
    }
    asked_for_all=TRUE;
    return NOERROR;
}

int all_ain()
{
	uint8 *sendBuff, *recBuff;
	uint16 checksumTotal, bits16;
	uint32 bits32;

	int sendChars, recChars, i, j, sendSize, recSize;
	int ret = 0;

	for( i = 0; i < 14; i++ )
	U6_state.AINs[i] = 9999;


	//Setting up Feedback command that will run numIterations times
	if( ((sendSize = 7+numChannels*4) % 2) != 0 )
	sendSize++;
	sendBuff = malloc(sendSize*sizeof(uint8)); //Creating an array of size sendSize

	if( ((recSize = 9+numChannels*3) % 2) != 0 )
	recSize++;
	recBuff = malloc(recSize*sizeof(uint8));   //Creating an array of size recSize

	sendBuff[1] = (uint8)(0xF8);     //Command byte
	sendBuff[2] = (sendSize - 6)/2;  //Number of data words
	sendBuff[3] = (uint8)(0x00);     //Extended command number

	sendBuff[6] = 0;     //Echo

	//Setting AIN read commands
	for( j = 0; j < numChannels; j++ )
	{
	sendBuff[7 + j*4] = 2;     //IOType is AIN24

	//Positive Channel (bits 0 - 4), LongSettling (bit 6) and QuickSample (bit 7)
	sendBuff[8 + j*4] = j; //Positive Channel
	sendBuff[9 + j*4] = (uint8)(resolution&15) + (uint8)((gainIndex&15)*16);   //ResolutionIndex(Bits 0-3), GainIndex(Bits 4-7)
	sendBuff[10 + j*4] = (uint8)(settlingFactor&7);  //SettlingFactor(Bits 0-2)
	if( j%2 == 0 )
	    sendBuff[10 + j*4] += (uint8)((differential&1)*128);   //Differential(Bits 7)
	}

	extendedChecksum(sendBuff, sendSize);

	//Sending command to U6
	if( (sendChars = LJUSB_Write(hDevice, sendBuff, sendSize)) < sendSize )
	{
	    if(sendChars == 0)
		printf("Feedback error (Iteration %d): write failed\n", i);
	    else
		printf("Feedback error (Iteration %d): did not write all of the buffer\n", i);
	    ret = -1;
	    goto cleanmem;
	}

	//Reading response from U6
	if( (recChars = LJUSB_Read(hDevice, recBuff, recSize)) < recSize )
	{
	    if( recChars == 0 )
	    {
		printf("Feedback error (Iteration %d): read failed\n", i);
		ret = -1;
		goto cleanmem;
	    }
	}

	checksumTotal = extendedChecksum16(recBuff, recChars);
	if( (uint8)((checksumTotal / 256) & 0xff) != recBuff[5] )
	{
	    printf("Feedback error (Iteration %d): read buffer has bad checksum16(MSB)\n", i);
	    ret = -1;
	    goto cleanmem;
	}

	if( (uint8)(checksumTotal & 0xff) != recBuff[4] )
	{
	    printf("Feedback error (Iteration %d): read buffer has bad checksum16(LBS)\n", i);
	    ret = -1;
	    goto cleanmem;
	}

	if( extendedChecksum8(recBuff) != recBuff[0] )
	{
	    printf("Feedback error (Iteration %d): read buffer has bad checksum8\n", i);
	    ret = -1;
	    goto cleanmem;
	}

	if( recBuff[1] != (uint8)(0xF8) || recBuff[3] != (uint8)(0x00) )
	{
	    printf("Feedback error (Iteration %d): read buffer has wrong command bytes \n", i);
	    ret = -1;
	    goto cleanmem;
	}

	if( recBuff[6] != 0 )
	{
	    printf("Feedback error (Iteration %d): received errorcode %d for frame %d in Feedback response. \n", i, recBuff[6], recBuff[7]);
	    ret = -1;
	    goto cleanmem;
	}

	if( recChars != recSize )
	{
	    printf("Feedback error (Iteration %d): received packet if %d size when expecting %d\n", i, recChars, recSize);
	    ret = -1;
	    goto cleanmem;
	}

	//Getting AIN voltages
	for(j = 0; j < numChannels; j++)
	{
	    bits32 = recBuff[9+j*3] + recBuff[10+j*3]*256 + recBuff[11+j*3]*65536;
	    getAinVoltCalibrated(&calInfo, resolution, gainIndex, 1, bits32, &U6_state.AINs[j]);
	}
  
    for( j = 0; j < numChannels; j++ )
        printf("%.3lf\n", U6_state.AINs[j]);

cleanmem:
    free(sendBuff);
    free(recBuff);
    sendBuff = NULL;
    recBuff = NULL;

    return ret;
}
