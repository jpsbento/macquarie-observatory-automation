/* Java Script */

var Out;

sky6Dome.Connect();

if (sky6Dome.IsGotoComplete==0)/*Connect failed for some reason*/

{

Out = "Not Completed"

}

else

{

Out = "Done"

}

