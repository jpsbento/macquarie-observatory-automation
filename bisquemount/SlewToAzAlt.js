/* Java Script */

var TargetAz = "53.2";
var TargetAlt = "20";
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


