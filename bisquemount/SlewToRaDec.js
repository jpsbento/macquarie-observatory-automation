/* Java Script */

var TargetRa = "16.490125326609146";
var TargetDec = "-26.43209515860898";
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
