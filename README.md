# mappy

this is a bunch of python programs for putting/getting imessages on
raspberry pi to/from an apple device capable of message access profile 
(MAP) over bluetooth.  only tested with iPad Pro + ipados16.7 but it should
work with other newish idevices with ios 8 and above.  i am aware that
some android devices support MAP so maybe these progs could also work
(or be made to work) with android hardware.

WARNING. this software can result in contact details and/or sensitive
message content being transmitted on bluetooth airwaves that could be
intercepted.

intended use.
  suppose you have a raspberry pi without keyboard or monitor running
on battery withohut wifi signal.  the pi has booted into a python prog
that is measuring something.  it would be nice if the pi could tell your
iPad "hum.py running... humidity=57%".  these tools allow you to do this
without any need to write code for the iPad.  it is also possible to
send a message from iPad to a prog running on pi.  if you send an
imessage to yourself on the ipad (after attempting to upload to icloud
for upto 9 minutes) the message arrives in inbox.  if message notification
server (MNS) is live on pi, it gets a notification saying "new message"
which can then be read.  the long delay is annoying.  if wifi is available
then there is little delay, but with wifi there are better ways of doing
ipad <-> raspberry comms.

alternative uses (with extra code).
  receive incomming messages and translate or display in large font or
convert to audio.  compose messages on big screen with nice keyboard. 
the MAP specification suggests that data other than text (eg sound samples)
could be embedded in/attached to messages but it is not clear how.
if a message on ipad has an attachment, the attachment does not go through
the MAP transfer.

all the code here needs some information to work - namely the bd_addr
of the idevice and the RFCOMM channel that the MAP service uses.
turn on bluetooth.  in the pi terminal run `hcitool scan`.  this gives the
bd_addr of the ipad/iphone.  then execute  
`sdptool browse --uuid 0x1134 <bd_addr>`
where <bd_addr> is the string of colon-separated hex digit pairs that
identify your idevice.  in the output you should see RFCOMM, beneath
which is the channel number you need.  patch this info into 
puttxt.py putj.py listinbox.py getmsg.py mns.py where you see  
#EDIT NEXT 2 LINES ...  
ma.py on its own does not do anything. it is used by the other progs.
ma.py and mns.py use obx_const.py.

pair idevice with raspberry before running the python scripts.
mns.py should be preceded by `sudo hciconfig hci0 piscan` and also
needs sudo privilege to advertise.

### notte benne
the first time you run one of these progs on the pi, it will most
likely fail with error "obex connect failed".  this is normal.
to fix: on idevice go settings->bluetooth.  see the line that says
raspberry pi connected (or similar). tap on little blue i in circle.
tap enable notifications.  reboot idevice.  turn bluetooth on again.
MAP connection should now work.

good practice to turn off bluetooth when done.  if you don't want 
pi-generated messages going to icloud and perhaps forwarded to others,
do the MAP stuff with wifi off and delete them before wifi switched 
back on. 

requirements.
python 3.x.
pybluez.
