/* Java Script */

var Out;

sky6Dome.Connect();

if (sky6Dome.IsGoToComplete==0)/*Connect failed for some reason*/
{

Out = "Not Completed"

}

else

{

Out = "Done"

}

