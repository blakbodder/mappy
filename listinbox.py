from ma import *

#EDIT NEXT 2 LINES so bd_addr is that of server device and channel it uses
IPAD="AA:BB:CC:DD:EE:FF"
channel=2       #RFCOMM channel that MA server uses

def fragment(ting):
    sting = str(ting,'utf-8')
    frags = sting[31:-18].split('<')
    for frag in frags:  print(frag[:-2],'\n')

macli = MAClient(IPAD,channel)
macli.connect()
macli.setpath("telecom", 2)
macli.setpath("msg", 2)
macli.setpath("inbox", 2)
ting = macli.get("x-bt/MAP-msg-listing")
#print(str(ting,'utf-8'))
fragment(ting)
macli.disconnect()
# in theory it is possible to get a filtered listing
# eg only unread msgs or from particular sender
# see MAP specification for relevant ap params
