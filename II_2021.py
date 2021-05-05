#!/usr/bin/python
# -*- coding: utf-8 -*-
 
# The modules required
import sys
import socket
from struct import unpack, pack, calcsize
import random
import string

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

BUFFERSIZE = 2048
FS = "!8s??hh128s"

enc_keylist = []
dec_keylist = []


def send_and_receive_tcp(address, port, message):
    """ TCP communication
    """
    # counters for sent and received messages
    scount = 0
    rcount = 0

    print("You gave arguments: {} {} {}".format(address, port, message))
    
    tcp_msg = message
    
    # create TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect socket to given address and port
    tcp_socket.connect((address, port))

    # adds the ending to the message
    tcp_msg += "\r\n"

    # ******    IF ENCRYPTION           **********
    if "ENC" in message:
        print("ENC = TRUE")
        # generates keys and adds them to message
        tcp_msg += generate_keys()

    # *******   ENCRYPTION PART ENDS    **********

    # send message
    tcp_socket.sendall(tcp_msg.encode())
    scount += 1
    print("CLIENT (TCP, {}):    {}".format(scount, message))        # keys not printed

    # receive data from socket
    msg_recv = tcp_socket.recv(BUFFERSIZE).decode()

    # ******    IF ENCRYPTION           **********
    if "ENC" in message:
        global dec_keylist
        dec_keylist = msg_recv.split("\r\n")[:21] 
        msg_recv = dec_keylist.pop(0)

    # *******   ENCRYPTION PART ENDS    **********

    # print received message without keys
    rcount += 1
    print("SERVER (TCP, {}):    {}".format(rcount, msg_recv))

    # close the socket
    tcp_socket.close()
    
    # Get your CID and UDP port from the message
    cid, udp_port = msg_recv.split(" ")[1:]
    udp_port = int(udp_port)

    # Continue to UDP messaging
    send_and_receive_udp(address, udp_port, cid, message)

    return
 
 
def send_and_receive_udp(address, port, cid, tcp_msg):
    """ UDP communication
    """
    # counters for sent and received messages
    scount = 0
    rcount = 0
    # init end of message as false
    eom = False

    # creates udp socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    msg = "Hello from {}".format(cid)

    # loop
    while True:
        # ******    ENCRYPT STARTS      ******

        if "ENC" in tcp_msg:
            try:
                key = enc_keylist.pop(0)
                enc_msg = crypt_msg(msg, key)
            
            except IndexError:
                print("No more keys. Messages are no longer encrypted.")
        
        # ******    ENCRYPT STOPS       ******

        # creates packet
        packet = form_udp_packet(cid, enc_msg)
                
        # sends packet
        sent_bytes = udp_socket.sendto(packet, (address, port))
        assert sent_bytes == calcsize(FS), "All bytes not sent"
        scount += 1
        print("CLIENT (UDP, {}):    {}".format(scount, msg))

        # receives packet
        packet_recv = udp_socket.recv(BUFFERSIZE)
        # reads the message from the received packet
        eom, msg_recv = unpack_udp_packet(packet_recv)


        # ******    DECRYPT STARTS      ******

        if ("ENC" in tcp_msg) and not eom:
            try:
                key = dec_keylist.pop(0)
                msg_recv = crypt_msg(msg_recv, key)
            
            except IndexError:
                pass
        
            assert (msg_recv[0] in string.ascii_lowercase), "decrypting gone wrong"

        # ******    DECRYPT STOPS       ******
        rcount += 1
        print("SERVER (UDP, {}):    {}".format(rcount, msg_recv))

        # break the loop
        if eom:
            break
        
        msg = reverse_words(msg_recv)
    
    return
    
 
def form_udp_packet(cid, content):
    """ Forms the UDP-packet
    """
    # calculates the message lenght
    msg_len = len(content)
    # packs the data
    data = pack(FS, cid.encode(), True, True, 0, msg_len, content.encode())
    return data

def unpack_udp_packet(packet):
    """ Unpacks the UDP-packet
    """
    # unpack packet
    cid, ack, eom, dr, cl, content = unpack(FS, packet)
    # return content without padding
    return eom, content.decode()[:cl]

def reverse_words(msg):
    """ Reverses words separated by space.
    """
    # creates list from words
    words = msg.split(" ")
    
    # happens usually when decryption is wrong
    assert len(words) > 1, "only one word to reverse, could be decrypting gone wrong"
    # reverses list
    words.reverse()
    # makes a string from list
    msg = " ".join(words)
    
    return msg

def generate_keys():
    """ Function for generating encryption keys.
    """
    KEYCOUNT = 20
    KEYLENGTH = 64

    letters = string.ascii_lowercase
    msg = ""

    for _ in range(KEYCOUNT):
        # generate and save key
        key = "".join(random.choices(letters, k=KEYLENGTH))
        enc_keylist.append(key)

        # add to the message
        msg += key + "\r\n"

    msg += ".\r\n"

    return msg

def crypt_msg(msg, key):
    """ Encrypts or decrypts message with given key.
    """
    cr_msg = ""
    for a, b in zip(msg, key):
        cr_msg += chr(ord(a) ^ ord(b))
    
    return cr_msg

 
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
