#!/usr/bin/python
'''GBN Receiver'''

import struct
import sys
import socket

'''Create a socket and bind to the OS assigned port'''
def create_socket():
    sock = socket.socket(socket.AF_INET,
                        socket.SOCK_DGRAM) # UDP
    sock.bind(('', 0))

    '''Write to file for channel setup'''
    f = open('recvInfo', 'w')
    hostname = sock.getsockname()
    f.write(socket.gethostname() + " " + str(hostname[1]))
    f.close()

    '''Setup file for writing data to'''
    f = open(sys.argv[1], 'w') 

    '''Ready to receive'''
    expected_seq_num = 0
    while True:
    	data, address = sock.recvfrom(512)
    	udp_header = struct.unpack('!III', data[0:12])

	'''Check Packet Sequence Number'''
	if (udp_header[2] == expected_seq_num):

		'''Receive EOT Packet'''
		if (udp_header[0] == 2):

			packet_type = 2
			packet_length = 12
			packet_sequence_num = 99999
			print("PKT RECV EOT %d %d" % (udp_header[1], udp_header[2]))
			eot_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
			sock.sendto(eot_header, (address[0], int(address[1])))
			print("PKT SEND EOT %d %d" % (packet_length, packet_sequence_num))
			'''Close the socket'''
			print("Closing socket")
			sock.close()
			f.close()
			return

		'''Receive Data Packet'''
		if (udp_header[0] == 0):
			f.write(data[12:])
			'''Create ACK'''
			packet_type = 1
			packet_length = 12
			packet_sequence_num = udp_header[2]
			print("PKT RECV DAT %d %d" % (udp_header[1], udp_header[2]))
			ack_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
			sock.sendto(ack_header, (address[0], int(address[1])))
			print("PKT SEND ACK %d %d" % (packet_length, packet_sequence_num))
			expected_seq_num+=1
	'''EOT Packet'''
	if (udp_header[0] == 2):
		print("PKT RECV EOT %d %d" % (udp_header[1], udp_header[2]))
		packet_type = 2
		packet_length = 12
		packet_sequence_num = 99999
		eot_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
		sock.sendto(eot_header, (address[0], int(address[1])))
		print("PKT SEND EOT %d %d" % (packet_length, packet_sequence_num))
		'''Close the socket'''
		sock.close()
		f.close()
		return
	else:
		'''Resend most recent ACK'''
		packet_type = 1
		packet_length = 12
		packet_sequence_num = (expected_seq_num - 1)
		ack_header = struct.pack('!III', packet_type, packet_length, packet_sequence_num)
		sock.sendto(ack_header, (address[0], int(address[1])))
		print("PKT SEND ACK %d %d" % (packet_length, packet_sequence_num))

create_socket()

