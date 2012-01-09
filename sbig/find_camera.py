import sbigudrv as sb
sb.SBIGUnivDrvCommand(sb.CC_OPEN_DRIVER, None,None)
r = sb.QueryUSBResults()
sb.SBIGUnivDrvCommand(sb.CC_QUERY_USB, None,r)
r.camerasFound
sb.SBIGUnivDrvCommand(sb.CC_CLOSE_DRIVER, None,None)
