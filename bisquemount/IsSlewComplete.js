/* Java Script */

var Out;

sky6RASCOMTele.Connect();
sky6RASCOMTele.Asynchronous = true;

if (sky6RASCOMTele.IsSlewComplete==0)/*Connect failed for some reason*/

{

Out = "Not Completed"

}

else

{

Out = "Done"

}

