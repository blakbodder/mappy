# if not working try sudo hciconfig hci0 piscan
# before running:  sudo hciconfig hci0 piscan
# sudo python mns.py
import bluetooth
from ma import *
from select import poll, POLLIN
from time import sleep

#EDIT NEXT 2 LINES to match idevice bd_addr and MAP service channel
IPAD="AA:BB:CC:DD:EE:FF"
channel=2      #RFCOMM channel that MA server uses

class MNS(object):

    def __init__(self):
        port = 0x11
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.bind(("",port))
        self.sock.listen(1)
        #uuid = "bb582b41-420c-11db-b0de-0800200c9a66"
        uuid = "00001133-0000-1000-8000-00805f9b34fb"
        bluetooth.advertise_service(self.sock, "MAP MNS-rasp", uuid, ["1133"],
             [("1133",0x104)], "", "message notification service",["0008"])

    def poll_incoming(self):
        polist = self.p.poll(0)     # immediate return
        for fd,flags in polist:
            if fd==self.noosk_fd:
                dat = self.noosk.recv(self.max_pkt_len)
                # TODO check for disconnect
                self.noosk.send(b'\xa0\x00\x03')
                k = dat.find(b'handle')
                if k>0:
                    sp = dat[k+6:k+30].split(b'"')
                    #print(sp)
                    hndl = str(sp[1], 'utf-8')
                    print("fetching", hndl)
                    bmsg = macli.get("x-bt/message", name=hndl)
                    print(str(bmsg, 'utf-8'))

            elif fd==0:
                ip = input()
                if ip == "q":
                    macli.disconnect()
                    quit()

    def start(self):
        print("waiting MNS connection")
        self.noosk,addr = self.sock.accept()
        print(addr, "connected.")
        self.max_pkt_len = 2048
        ver_flag_pktlen = b'\x10\x00\x08\x00'	# pktlen=2048
        self.cnnctidhdr = b'\xcb\x7b\xd1\x37\xdf'
        who = b'\xbb\x58\x2b\x41\x42\x0c\x11\xdb\xb0\xde\x08\x00\x20\x0c\x9a\x66'
        req = self.noosk.recv(self.max_pkt_len)
        dump(req)
        if req[0] == 0x80 and len(req) >= 7:
            self.remote_pkt_len =  256*req[5] + req[6]
            print("remote pkt len =", self.remote_pkt_len)
            whohdr = self.who_header(who)
            self.send_response(0xa0,ver_flag_pktlen+self.cnnctidhdr+whohdr)
            print("obex connect ok")
            bluetooth.stop_advertising(self.sock)

            # polling bt socket allows other stuff to be done
            self.noosk_fd = self.noosk.fileno()
            self.p = poll()
            self.p.register(0, POLLIN)
            self.p.register(self.noosk_fd, POLLIN)
            print("q<RET> to quit")

            while True:
                self.poll_incoming()
                sleep(0.1)

        else:  print("bad request")

    def send_response(self, rsp, hdrs):
        l = len(hdrs)+3
        if l > self.remote_pkt_len:  print("PROBLEM.  remote pkt len exceded")
        resp = pack('>BH', rsp, l) + hdrs
        self.noosk.send(resp)

    def who_header(self, bdat):
        l = len(bdat)+3
        hid = WHO_HDR | BITES
        hdr = pack('>BH', hid, l) + bdat
        return hdr

mns = MNS()
macli = MAClient(IPAD, channel)
macli.connect()
macli.register_notify(b'\x0e\x01\x01')	 # notify on
mns.start()
# to stop being notified : macli.register_notify(b'\x0e\x01\x00')
