/* Java Script */

var TargetRa = "12.443294451593072";
var TargetDec = "-63.09915374219697";
var Out;

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)//Connect failed for some reason
{
	Out = "Not connected"
}
else
{
	sky6RASCOMTele.Asynchronous = true;
	sky6RASCOMTele.SlewToRaDec(TargetRa, TargetDec,"");
	Out  = "OK";
}
