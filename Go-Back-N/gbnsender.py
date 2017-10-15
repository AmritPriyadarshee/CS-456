#!/usr/bin/python
import socket
import struct
import sys
import time

sequence_num = 0
window = []
window_size = 10
base = 0

f = open(sys.argv[2], 'rb')
data = None
done = False

channelInfo = open('channelInfo', 'r')
x = channelInfo.read()
y = x.split()
hostname = y[0]
port = y[1]

mostrecentAck = time.time()

timeout = float(sys.argv[1])
timeout = float(timeout/1000)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 0))
s.settimeout(timeout)
while not done or window:
	'''Go through 500 byte segments and send'''
	'''While window isn't full and not EOF'''
	if (sequence_num < window_size + base) and (data != ""):
		data = f.read(500)
		packet_type = 0
		packet_length = len(data) + 12
		packet_sequence_num = sequence_num

		udp_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
		s.sendto(udp_header + data, (str(hostname), int(port)))

		print("PKT SEND DAT %d %d" % (packet_length, packet_sequence_num))
		sequence_num = (sequence_num + 1)		
		
		'''Add the packet we just sent to the window'''
		window.append(udp_header + data)
		
		'''If we're done reading, exit the loop by setting the boolean to be True'''
		if (not data):
			done = True
			'''Send EOT packet'''
			packet_type = 2
			packet_length = 12
			packet_sequence_num = sequence_num
			eot_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
			s.sendto(eot_header, (str(hostname), int(port)))
			sequence_num= (sequence_num + 1)

			print("PKT SEND EOT %d %d" % (packet_length, packet_sequence_num))
			'''Add the packet we just sent to the window'''
			window.append(udp_header + data)
			data = f.read(500)

	try:
		data, address = s.recvfrom(12)
		udp_header = struct.unpack('!III', data[0:12])
		rec_packet_type = udp_header[0]
		rec_packet_length = udp_header[1]
		rec_packet_sequence_num = udp_header[2]
		if (rec_packet_sequence_num == 99999):
			print("PKT RCV EOT %d %d" % (rec_packet_length, rec_packet_sequence_num))
			window = []
			s.close()
			f.close()

		while (rec_packet_sequence_num >= base) and window:
			print("PKT RECV ACK 12 %d" % rec_packet_sequence_num)

			lwindow = window[0]
			lwindow_header = struct.unpack('!III', lwindow[0:12])
			lwindow_seq = lwindow_header[2]

			while (lwindow_seq <= rec_packet_sequence_num):
				mostrecentAck = time.time()
				
				todel = window[0]
				todel_h = struct.unpack('!III', lwindow[0:12])
				del window[0]
				base= (base + 1)

				'''Annoying way of updating stuff b/c Python wasn't being normal'''
				lwindow = window[0]
				lwindow_header = struct.unpack('!III', lwindow[0:12])
				lwindow_seq = lwindow_header[2]

	except:
		if (time.time() - mostrecentAck > timeout):
			for i in range(len(window)):
				x = window[i]
				resend_packet = struct.unpack('!III', x[0:12])
				print("PKT SEND DAT %d %d" % (resend_packet[1], resend_packet[2]))
				s.sendto(window[i], (str(hostname), int(port)))
	
