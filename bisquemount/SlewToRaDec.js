/* Java Script */

var TargetRa = "6.399202440132903";
var TargetDec = "-52.695567149682894";
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
