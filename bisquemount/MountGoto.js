/* Java Script */

var TargetRA = "46";
var TargetDec = "-80";
var Out;

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.Asynchronous = true;
	sky6RASCOMTele.SlewToRaDec(TargetRA, TargetDec,"");
	Out  = "OK";
}
