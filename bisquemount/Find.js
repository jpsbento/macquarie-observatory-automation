/* Java Script */var Out;
var PropCnt = 189; Out = "";
sky6StarChart.Find("Acrux");
for(p=0;p<PropCnt;++p) {if(sky6ObjectInformation.PropertyApplies(p) != 0){sky6ObjectInformation.Property(p) ;Out+=sky6ObjectInformation.ObjInfoPropOut;Out+=';'}}
