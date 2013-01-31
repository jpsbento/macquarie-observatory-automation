/* Java Script */

var dJog = "-2.3363";
var dDirection = "East";
var Out;


sky6RASCOMTele.Connect();



if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.Jog(dJog, dDirection);
	Out  = "OK";
}


