# origionally this was an attempt to upload .jpeg to MAP server.
# the idea was to prepend a MIME header to a base64 encoded jpeg
# but this did not work.  also tried wrapping jpeg in a html file
# then upload,copy/paste/save to files but safari could not access
# now this just converts <filename> to bmsg and puts to imessage

import sys
from ma import *

#EDIT NEXT TWO LINES to match your idevice bdaddr and MAP server channel
IPAD="AA:BB:CC:DD:EE:FF"
channel=2       #RFCOMM channel that MA server uses

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

def mime_header(name):
	header = b'MIME-Version: 1.0\r\n'
	header += b'Content-Type: image/jpeg\r\n'
	header += b'Content-Disposition: attachment; filename=' + bytes(name,'utf-8') + b';\r\n'
	header += b'Content-Transfer-Encoding: base64\r\n\r\n'
#	print(header)
	return header

if len(sys.argv)==2:
	filename = sys.argv[1]
else:
	print("usage: python putj.py <filename>")

#mh = mime_header(filename)

macli = MAClient(IPAD,channel)
macli.connect()
macli.setpath("telecom", 2)
macli.setpath("msg", 2)
macli.setpath("outbox", 2)
hndl = macli.jput(filename, prelude, postlude)
print("hadle=", hndl)
macli.disconnect()
