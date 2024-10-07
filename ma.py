# message access client - read/upload msgs to imessage on ipad/iphone
import bluetooth, sys, os, stat
from struct import pack,unpack
from obx_const import *

bmauuid = b'\xbb\x58\x2b\x40\x42\x0c\x11\xdb\xb0\xde\x08\x00\x20\x0c\x9a\x66'

def dump(data):
	n = len(data)
	print("len=",n)
	nib="0123456789abcdef"
	i=0
	while i<n:
		hex=""
		s=""
		k = i+16
		if k>n:  k=n
		while i < k:
			d = int(data[i])
			hi = d>>4
			lo = d & 0x0f;
			hex += nib[hi]
			hex += nib[lo]
			hex += ' '
			if d<0x20 or d>0x7e:  c ='.'
			else: c = chr(d)
			s += c
			i+=1
		print(hex, s)

class MAClient(object):

	def __init__(self, bdaddr, chan):
		self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.max_pkt_len = 2048
		self.remote_max_pkt_len = 2048 # provisional
		print("connecting...")
		self.sock.connect((bdaddr, chan))
		print("ok")

	def connect(self):	# OBEX connect + target header
		ver_flag_pklen = b'\x10\x00\x08\x00'	 # x08 x00 == 2048
		trghdr = self.target_header(bmauuid)
		self.send_request(0x80, ver_flag_pklen + trghdr)
		resp = self.sock.recv(self.max_pkt_len)
		dump(resp)
		if len(resp)>=7 and resp[0] == 0xa0:
			print("obex connect ok")
			# remote max pkt len (big-endian) in resp[5..7]
			self.remote_max_pkt_len = resp[5]*256 + resp[6]
			print("rmpktlen=", self.remote_max_pkt_len)
			# try extract connection id
			if len(resp)>=12 and resp[7]==0xcb:
				self.cnnctidhdr = resp[7:12]
				#print(self.cnnctidhdr)
			#else report error
		else:  print("obex connect failed")

	def get(self, tipe, ap=None, name=None, save=False):
		self.bytes_received=0
		self.sigma_bod = b''
		hdr0 = self.type_header(tipe)
		if name:
			hdr1 = self.name_header(name)
			if ap:
				hdr2 = self.ap_param_header(ap)
				self.send_request(0x83, self.cnnctidhdr+hdr0+hdr1+hdr2)
			else:  self.send_request(0x83, self.cnnctidhdr+hdr0+hdr1)
		else:
			self.send_request(0x83, self.cnnctidhdr + hdr0)

		self.receive()
#		dump(self.data)
		status = self.parse_data()
		if save:  getfile = open("dummyname.txt","wb")
		file_len = 1000000	#  TODO extract length
		notdone = True
		while notdone:
			if status & (BODY_BIT | END_OF_BODY_BIT):
				bod_end = self.bod_start + self.bod_len
				bod = self.data[self.bod_start : bod_end]
				if save: getfile.write(bod)
				else:  self.sigma_bod += bod
				self.bytes_received += self.bod_len
				# complete when end_of_bod or bytes_received==file_len
				notdone =  not ((status & END_OF_BODY_BIT) or self.bytes_received >= file_len)
				if notdone:	# get more
					self.sock.send(self.req)
					self.receive()
					status = self.parse_data()
				else:
					if save:  getfile.close()
					return self.sigma_bod

			else:  print("what? no body.");  return self.sigma_bod

	def shortmsgput(self, bmsg):	# should be in telecom/msg/outbox
		hdr0 = self.type_header("x-bt/message")
		hdr1 = self.target_header(b'\x14\x01\x01')
		hdr2 = self.body_header(bmsg, True)
		self.send_request(0x82, self.cnnctidhdr+hdr0+hdr1+hdr2)
		resp = self.sock.recv(self.max_pkt_len)
		if resp[0]==0xa0:  print("put ok")
		return self.extract_handle(resp)

	def jput(self, filename, prelude, postlude, mimehdr=b''):
		file = open(filename, 'rb')
		bytesleft = filelen = os.stat(filename)[stat.ST_SIZE]
		hdr0 = self.type_header("x-bt/message")
		hdr1 = self.target_header(b'\x14\x01\x01')
		#hdr1 = self.target_header(b'\x0a\x01\x01')
		bod = prelude
		mlen = filelen + 22 + len(mimehdr)
		bod += b'LENGTH:' + bytes(str(mlen), 'utf-8') +b'\r\n'
		bod += b'BEGIN:MSG\r\n' + mimehdr
		while bytesleft:
			chunk = file.read(3500)
			bytesread=len(chunk);  bytesleft-=bytesread
			#print("bytes left=", bytesleft)
			bod += chunk
			if bytesleft:
				hdr2 = self.body_header(bod, False)
				self.send_request(0x02, self.cnnctidhdr+hdr2)
				resp = self.sock.recv(self.max_pkt_len)
				#dump(resp)
				if resp[0] != 0x90:
					print("oh oh")
					file.close()
					break
				bod = b''
			else:
				bod += b'\r\n' + b'END:MSG\r\n' + postlude
				hdr2 = self.body_header(bod, True)
				self.send_request(0x82, self.cnnctidhdr+hdr0+hdr1+hdr2)
				resp = self.sock.recv(self.max_pkt_len)
				file.close()
				if resp[0] == 0xa0:
					print("jput ok")
					return self.extract_handle(resp)
				else:  dump(resp);  return None

	def register_notify(self, ap):
		hdr0 = self.type_header("x-bt/MAP-NotificationRegistration")
		hdr1 = self.ap_param_header(ap)
		hdr2 = b'\x49\x00\x04\x30'	# endofbod with filler
		self.send_request(0x82,  self.cnnctidhdr+hdr0+hdr1+hdr2)
		resp = self.sock.recv(self.max_pkt_len)
		if resp[0]==0x0a:  print("register notify ok")

# an obex response pkt may be split over several physical pkts so re-assemble
# it may be possible to recv bigger pkts with .setsockopt()
	def receive(self):
		self.data = self.sock.recv(self.max_pkt_len)
		obxlen = self.ntohs(1)
		while len(self.data) < obxlen:
			self.data += self.sock.recv(self.max_pkt_len)

	def setpath(self, pathname, flag=0):
		if pathname:
			hdr0 = self.name_header(pathname)
			l = len(hdr0) + 10
			req = pack('>BHBB', 0x85, l , flag, 0) + self.cnnctidhdr + hdr0
		else :
			req =  b'\x85\x00\x0a' + pack('BB', flag, 0) + self.cnnctidhdr
		self.sock.send(req)
		resp = self.sock.recv(self.max_pkt_len)
		if resp[0] == 0xa0:  print("setpath ok")

	def name_header(self, filename):
		u = bytes(filename,'utf-16-be') + b'\x00\x00'
		#u = bytes(filename, 'utf-8')
		#print(u)
		hid = NAME_HDR | UNICODE
		l = len(u)+3
		hdr = pack('>BH', hid, l) + u
		return hdr

	def length_header(self, len):
		hid = LENGTH_HDR | FOURBYTE
		hdr = pack('>BI', hid, len)
		return hdr

	def body_header(self, buff, endof):
		if endof :  hid = END_OF_BODY_HDR | BITES
		else:  hid = BODY_HDR | BITES
		hdr = pack('>BH', hid, len(buff)+3) + buff
		return hdr

	def target_header(self, bdata):
		hid = TARGET_HDR | BITES
		hdr = pack('>BH', hid, len(bdata)+3) + bdata
		return hdr

	def type_header(self, string):
		hid = TYPE_HDR | BITES
		bstr = bytes(string, 'utf-8') +b'\x00'
		hdr = pack('>BH', hid, len(bstr)+3) + bstr
		return hdr

	def ap_param_header(self, bdata):
		hid = APP_PARAMS_HDR | BITES
		hdr = pack('>BH', hid, len(bdata)+3) +bdata
		return hdr

	# to send several headers, concatenate a la
	# macli.send_request(opcode, hdr0 + hdr1 + ...)
	def send_request(self, opcode, hdrs):
		l = len(hdrs)+3		# total length
		if l > self.remote_max_pkt_len:
			print("ERROR.  remote_max_pkt_len exceded")
			# should handle gracefully
		self.req = pack('>BH', opcode, l) + hdrs
		self.sock.send(self.req)

	def parse_data(self):
		#print("parse")
		if (self.data[0] == 0xa0) or (self.data[0] == 0x90):	# if success
			status=0
			k=3
			left=len(self.data)-3
			#print("left=", left)
			while left>0:
				hid = self.data[k]
				typebits = hid & 0xc0
				hid &= 0x3f
				if hid == NAME_HDR:
					l16 = self.ntohs(k+1)
					self.name = str(self.data[k+3: k+l16],'utf-16-be')
					status |= NAME_BIT
					k+=l16;  left-=l16
					#print("l16=", l16)
				elif hid == LENGTH_HDR:
					self.length= self.ntohl(k+1)
					status |= LENGTH_BIT
					k+=5;  left-=5
					#print(self.length)
				elif (hid == BODY_HDR) or (hid == END_OF_BODY_HDR):
					self.bod_start = k+3
					l16 = self.ntohs(k+1)
					self.bod_len = l16-3
					if hid==END_OF_BODY_HDR:  status |= END_OF_BODY_BIT
					else:  status |= BODY_BIT
					k+=l16;  left-=l16
					#print("after bod left=", left)
				else:
					print(lookup[hid], "header IGNORED")
					if (typebits == UNICODE) or (typebits == BITES):
						l16 = self.ntohs(k+1)
						k+=l16;  left-=l16
					elif typebits == FOURBYTES:
						k+=5;  left-=5
					else :
						k+=2;  left-=2

			return status
		else:
			print("no good")
			dump(self.data[:16])
			return FORBIDDEN_BIT

	def ntohs(self, k):	# 16 bit field len
		return self.data[k]*256 + self.data[k+1]

	def ntohl(self, k):	# 32 bit value
		q, = unpack('>I',self.data[k:k+4])
		return q

	def extract_handle(self, resp):
		left = len(resp)-3
		k=3;
		while left>0:
			hid = resp[k]
			typebits = hid &0xc0
			hid &= 0x3f
			if hid == NAME_HDR:
				l16 = resp[k+1]*256 + resp[k+2]
				handle =  str(resp[k+3:k+l16],'utf-16-be')
				return handle
			if (typebits == UNICODE) or (typebits == BITES):
				l16 = resp[k+1]*256 + resp[k+2]
				k+=l16;  left-=l16
			elif typebits == FOURBYTES:  k+=5;  left-=5
			else:  k+=2;  left-=2
		return None

	def disconnect(self):
		self.sock.send(b'\x81\x00\x08' + self.cnnctidhdr)
		resp = self.sock.recv(self.max_pkt_len)
		if resp[0]==0xa0:  print("disconnect ok")
		self.sock.close()
		self.sock=None
