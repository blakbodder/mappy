import sys
from ma import *

#EDIT NEXT TWO LINES to match your idevice bdaddr and MAP server channel
IPAD="AA:BB:CC:DD:EE:FF"
channel=2       #RFCOMM channel that MA server uses

if len(sys.argv)==2:
	msghandle = sys.argv[1]
else:
	print("usage: python getmsg.py <message handle>")

macli = MAClient(IPAD,channel)
macli.connect()
macli.setpath("telecom", 2)
macli.setpath("msg", 2)
macli.setpath("inbox", 2)
msg = macli.get("x-bt/message", name=msghandle)
print(str(msg,'utf-8'))
macli.disconnect()
