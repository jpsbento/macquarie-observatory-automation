/* Java Script */

var TargetAz = "90";
var TargetAlt = "40";
var Out;



sky6RASCOMTele.Connect();



if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.Asynchronous = true;
	sky6RASCOMTele.SlewToAzAlt(TargetAz, TargetAlt,"");
	Out  = "OK";
}


