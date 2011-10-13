/* Java Script */

var Out;

var Cmd = 9;

var Direction = 2;

var Rate = 10;

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/

{

Out = "Not connected"

}

else

{

var param = String(Direction)+"|"+String(Rate);

sky6RASCOMTele.DoCommand(Cmd,param);

Out = "OK"

}
