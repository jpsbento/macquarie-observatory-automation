/* Java Script */

var TargetAz = "30";
var TargetAlt = "30";
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


