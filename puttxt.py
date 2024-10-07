import sys
from ma import *

#EDIT NEXT TWO LINES to match your idevice bdaddr and MAP server channel
IPAD="AA:BB:CC:DD:EE:FF"
channel=2       #RFCOMM channel that MA server uses

# note the fictitious email address
# this could be changed either by manual edit or programatically
prelude = \
b'BEGIN:BMSG'  b'\r\n'  \
b'VERSION:1.0'   b'\r\n'   \
b'STATUS:UNREAD'   b'\r\n'  \
b'TYPE:EMAIL'   b'\r\n'  \
b'FOLDER:'   b'\r\n'   \
b'  BEGIN:BENV'   b'\r\n'  \
b'    BEGIN:VCARD'   b'\r\n'  \
b'      VERSION:2.1'  b'\r\n'  \
b'      N:anonymous'  b'\r\n'  \
b'      EMAIL:somebody@nowhere.org' b'\r\n'  \
b'    END:VCARD' b'\r\n'   \
b'    BEGIN:BBODY' b'\r\n'  \
b'      ENCODING:8BIT'  b'\r\n'

postlude = \
b'    END:BBODY'  b'\r\n' b'  END:BENV'  b'\r\n'  b'END:BMSG'  b'\r\n'

def txt_to_bmsg(text):
	mlen = len(text) + 22
	bmsg = prelude
	bmsg += b'      LENGTH:' + bytes(str(mlen), 'utf-8') + b'\r\n'
	bmsg += b'BEGIN:MSG\r\n' + bytes(text,'utf-8') + b'\r\n' + b'END:MSG\r\n'
	bmsg += postlude
	return bmsg

if len(sys.argv)==2:
	txt = sys.argv[1]
	print(txt)
else:
	print("usage:  python puttxt.py \"<message>\"")
	quit()

macli = MAClient(IPAD,channel)
macli.connect()
macli.setpath("telecom", 2)
macli.setpath("msg", 2)
macli.setpath("outbox", 2)
bm = txt_to_bmsg(txt)
#print(bm)
hndl=macli.shortmsgput(bm)
print("handle=",hndl)
macli.disconnect()
