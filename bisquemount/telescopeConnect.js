/* Java Script */

var Out;

sky6RASCOMTele.Connect();

if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/

{

Out = "Not connected"

}

else

{

Out = "OK"

}

