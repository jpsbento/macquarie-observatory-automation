/* Java Script */

var Out;
sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.GetAzAlt();
	Out  = String(sky6RASCOMTele.dAz) +" | " + String(sky6RASCOMTele.dAlt);
}
