/* Java Script */

var TargetRa = "16.490125119017343";
var TargetDec = "-26.43210227210159";
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
