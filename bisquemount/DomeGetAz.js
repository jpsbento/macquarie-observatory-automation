/* Java Script */

var Out;
sky6Dome.Connect();

if (sky6Dome.IsConnected==0)/*Connect failed for some reason*/
{
	Out = "Not connected to TheSky Virtual Dome"
}
else
{
	sky6Dome.GetAzEl();
	Out  = String(sky6Dome.dAz);
}
