#!/usr/bin/python
# -*- coding: utf-8 -*-
 
# The modules required
import sys
import socket
from struct import unpack, pack, calcsize

'''
This is a template that can be used in order to get started. 
It takes 3 commandline arguments and calls function send_and_receive_tcp.
in haapa7 you can execute this file with the command: 
python3 CourseWorkTemplate.py <ip> <port> <message> 

Functions send_and_receive_tcp contains some comments.
If you implement what the comments ask for you should be able to create 
a functioning TCP part of the course work with little hassle.  

''' 

# python coursework.py 195.148.20.105 10000 HELLO\r\n

BUFFERSIZE = 1024

def send_and_receive_tcp(address, port, message):
    """ TCP communication
    """

    print("You gave arguments: {} {} {}".format(address, port, message))
    # create TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect socket to given address and port
    tcp_socket.connect((address, port))

    # adds the ending to the message
    message += "\r\n"
    # send given message to socket
    tcp_socket.sendall(message.encode())
    # receive data from socket
    msg_recv = tcp_socket.recv(BUFFERSIZE).decode()
    # print received data
    print("RECEIVED MESSAGE:", msg_recv)
    
    # close the socket
    tcp_socket.close()
    
    # Get your CID and UDP port from the message
    cid, udp_port = msg_recv.split(" ")[1:]
    udp_port = int(udp_port)

    # Continue to UDP messaging
    message = "Hello from {}".format(cid)
    send_and_receive_udp(address, udp_port, cid, message)

    return
 
 
def send_and_receive_udp(address, port, cid, message):
    """ UDP communication
    """

    # creates udp socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # loop
    while True:
        print("SENDING MESSAGE:", message)

        # creates packet
        packet = form_udp_packet(cid, message)
        
        # unpacket = unpack_udp_packet(packet)
        # print("MY PACKET UNPACKED:", unpacket)
        

        # sends packet
        x = udp_socket.sendto(packet, (address, port))
        
        print("SENT BYTES:", x)
        # receives packet
        packet_recv = udp_socket.recv(BUFFERSIZE)
        # reads the message from the received packet
        msg_recv = unpack_udp_packet(packet_recv)
        print("RECEIVED MESSAGE:", msg_recv)

        # break the loop
        if "Bye" in msg_recv:
            break
        
        message = reverse_words(msg_recv)
    
    return
    
 
def form_udp_packet(cid, content):
    """ Forms the UDP-packet
    """
    # format string
    FS = "!8s??hh128s"
    # adds the ending string    ******** MAYBE NOT NEEDED WITH UDP ********
    # content += "\r\n"
    # calculates the message lenght
    msg_len = len(content)
    # packs the data
    data = pack(FS, cid.encode(), True, True, 0, msg_len, content.encode())
    return data

def unpack_udp_packet(packet):
    """ Unpacks the UDP-packet
    """
    # format string
    FS = "!8s??hh128s"
    # unpack packet
    cid, ack, eom, dr, cl, content = unpack(FS, packet)
    # return content without padding
    return content.decode()[:cl]

def reverse_words(msg):
    """ Reverses words separated by space.
    """
    # creates list from words
    words = msg.split(" ")
    # reverses list
    words.reverse()
    # makes a string from list
    msg = " ".join(words)
    
    return msg

 
def main():
    USAGE = 'usage: %s <server address> <server port> <message>' % sys.argv[0]
 
    try:
        # Get the server address, port and message from command line arguments
        server_address = str(sys.argv[1])
        server_tcpport = int(sys.argv[2])
        message = str(sys.argv[3])
    except IndexError:
        print("Index Error")
    except ValueError:
        print("Value Error")
    # Print usage instructions and exit if we didn't get proper arguments
        sys.exit(USAGE)
 
    send_and_receive_tcp(server_address, server_tcpport, message)
 
 
if __name__ == '__main__':
    # Call the main function when this script is executed
    main()
