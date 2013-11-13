/* Java Script */

var dJog = "0.0121942784132";
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


