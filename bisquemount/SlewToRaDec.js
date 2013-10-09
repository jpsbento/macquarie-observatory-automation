/* Java Script */

var TargetRa = "22.9609277778";
var TargetDec = "-28.3771388889";
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
