#!/usr/bin/python
# -*- coding: utf-8 -*-

# The modules required
import sys
import socket
from struct import unpack, pack, calcsize
import random
import string
from math import ceil

# This is a template that can be used in order to get started.
# It takes 3 commandline arguments and calls function send_and_receive_tcp.
# in haapa7 you can execute this file with the command:
# python3 CourseWorkTemplate.py <ip> <port> <message>

# Functions send_and_receive_tcp contains some comments.
# If you implement what the comments ask for you should be able to create
# a functioning TCP part of the course work with little hassle.


# python coursework.py 195.148.20.105 10000 HELLO\r\n

BUFFERSIZE = 2048       # size of the receive buffer
FS = "!8s??hh128s"      # format string for UDP-packet
ENC = PAR = False

enc_keylist = []        # encryption keys are stored here
dec_keylist = []        # decryption keys are stored here


def send_and_receive_tcp(address, port, msg):
    """ TCP communication
    """
    # counters for sent and received messages
    scount = rcount = 0
    # copy the original message
    og_msg = msg

    print("You gave arguments: {} {} {}".format(address, port, msg))

    # creates TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connects socket to given address and port
    tcp_socket.connect((address, port))

    # adds the ending to the message
    msg += "\r\n"

    # encryption
    if ENC:
        # generates keys and adds them to message
        msg += generate_keys()

    # sends message
    tcp_socket.sendall(msg.encode())
    scount += 1
    print("{:<22}{}".format("CLIENT (TCP, {}):".format(scount), og_msg))   # keys not printed
    # receive data from socket
    msg_recv = tcp_socket.recv(BUFFERSIZE).decode()

    # saves received keys for decryption
    if ENC:
        global dec_keylist
        dec_keylist = msg_recv.split("\r\n")[:-2]
        msg_recv = dec_keylist.pop(0)

    # prints received message without keys
    rcount += 1
    print("{:<22}{}".format("SERVER (TCP, {}):".format(rcount), msg_recv))

    # closes the socket
    tcp_socket.close()

    # get your CID and UDP port from the message
    cid, udp_port = msg_recv.split(" ")[1:]
    udp_port = int(udp_port)

    # continue to UDP messaging
    send_and_receive_udp(address, udp_port, cid)

    return


def send_and_receive_udp(address, port, cid):
    """ UDP communication
    """
    # counters for sent and received messages
    scount = rcount = 0
    # init end of message and acknowledgement
    eom, ack = False, True

    # creates the first message
    msg = "Hello from {}".format(cid)
    # creates udp socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # send and receive in a loop
    run = True
    while run:
        # prints the message that will be sent
        scount += 1
        print("{:<22}{}".format("CLIENT (UDP, {}):".format(scount), msg))    


        remain = len(msg)
        # splits message into parts for multipart messaging
        for piece in split_msg(msg):
            con_len = len(piece)    # length of piece
            remain -= con_len       # how much of message remaining

            # encryption
            if ENC and enc_keylist:
                key = enc_keylist.pop(0)
                piece = crypt_msg(piece, key)            
            # parity
            if PAR:
                piece = add_parity(piece)

            # creates packet
            packet = form_udp_packet(cid, ack, remain, con_len, piece)
            # sends packet
            sent_bytes = udp_socket.sendto(packet, (address, port))
            assert sent_bytes == calcsize(FS), "All bytes not sent"

        

        msg_recv = ""
        # receive multipart messages in a loop
        while True:
            # receives packet
            packet_recv = udp_socket.recv(BUFFERSIZE)
            # reads the message from the received packet
            eom, dr, piece_recv = unpack_udp_packet(packet_recv)
            msg_recv += piece_recv
            # stop receiving multipart messages
            if dr == 0:
                break
        
        # stop sending and receiving
        if eom:
            run = False
        # remove parity and decrypt the message
        else:
            if PAR:
                msg_recv, ack = check_parity(msg_recv)
                if not ack:
                    msg = "Send again"
            # decryption
            if ENC:
                temp = ""
                # decrypt in pieces
                for dec_piece in split_msg(msg_recv):
                    if dec_keylist:
                        key = dec_keylist.pop(0)
                        dec_piece = crypt_msg(dec_piece, key)
                    temp += dec_piece
                msg_recv = temp
        
        # print message if no errors found
        if ack:
            rcount += 1
            print("{:<22}{}".format("SERVER (UDP, {}):".format(rcount), msg_recv))
            msg = reverse_words(msg_recv)
        else:
            print("Received corrupted message from server.")
    return


def form_udp_packet(cid, ack, rm, con_len, content):
    """ Forms the UDP-packet
    """
    data = pack(FS, cid.encode(), ack, False, rm, con_len, content.encode())
    return data

def unpack_udp_packet(packet):
    """ Unpacks the UDP-packet
    """
    # unpack packet
    _, _, eom, dr, cl, content = unpack(FS, packet)
    # return content without padding
    return eom, dr, content.decode()[:cl]

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

def generate_keys():
    """ Function for generating encryption keys.
    """
    KEYCOUNT = 20       # amount of keys generated
    KEYLENGTH = 64      # length of a key

    letters = string.ascii_lowercase
    msg = ""
    for _ in range(KEYCOUNT):
        # generate and save key
        key = "".join(random.choices(letters, k=KEYLENGTH))
        enc_keylist.append(key)
        # add to the message
        msg += key + "\r\n"

    # ending of the message
    msg += ".\r\n"

    return msg

def crypt_msg(msg, key):
    """ Encrypts or decrypts message with given key.
    """
    cr_msg = ""
    for a, b in zip(msg, key):
        cr_msg += chr(ord(a) ^ ord(b))

    return cr_msg

def add_parity(msg):
    """ Adds parity bit to each character of a message.
    """
    new_msg = ""
    for ch in msg:
        n = ord(ch)
        n = (n << 1) + get_parity(n)
        new_msg += chr(n)
    return new_msg

def check_parity(msg):
    """ Checks parity and returns decoded message and ack if parity check passed. 
    """
    ack = True
    new_msg = ""
    for ch in msg:
        n = ord(ch)
        p = 1 & n
        n = n >> 1
        if p != get_parity(n):
            ack = False

        new_msg += chr(n)

    return new_msg, ack

def get_parity(n):
    """ Gets parity bit for number
    """
    while n > 1:
        n = (n >> 1) ^ (n & 1)
    return n

def split_msg(msg, length=64):
    """ Splits message into given length and returns list of pieces.
    """
    pieces = []
    for i in range(ceil(len(msg) / length)):
        pieces.append(msg[length*i:length*(i+1)])
    return pieces


def main():
    """ main function
    """
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

    # extra features
    global ENC, PAR
    ENC = "ENC" in message
    PAR = "PAR" in message
    send_and_receive_tcp(server_address, server_tcpport, message)


if __name__ == '__main__':
    # Call the main function when this script is executed
    main()
