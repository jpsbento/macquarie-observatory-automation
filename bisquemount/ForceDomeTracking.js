/* Java Script */

sky6Raven.Connect();

if (sky6Raven.IsConnected==0)/*Connect failed for some reason*/
{
	Out = "Not connected to TheSky Virtual Dome Raven object"
}
else
{
	sky6Raven.SlewDomeToTelescope();
}
