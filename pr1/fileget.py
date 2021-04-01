#!/usr/bin/env python3

import socket
import sys
import os
import re

# Checking arguments and splitting them to variables
if len(sys.argv) == 5:

    if sys.argv[1] == "-n":
        try:
            # needs to be IPv4:port
            re.search('^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):[0-9]*$', sys.argv[2]).group()
        except:
            print("\n\tIPv4 with port is not valid.\n")
            exit(1)
        ip = sys.argv[2].split(":")[0]
        port = int(sys.argv[2].split(":")[1])
        
    else:
        print("\n\tRun like: ./fileget.py -n <nameserver> -f <surl>\n")
        exit(1)

    if sys.argv[3] == "-f":
        try:
            # needs to be fsp://servername/filename
            re.search('^fsp:\/\/[\-\.\_0-9a-zA-Z]+\/', sys.argv[4]).group()
        except:
            print("\n\tSURL is not valid.\n")
            exit(1)

        fsp = sys.argv[4]
        server = fsp.split("/")[2]
        filename_init = fsp.split("/", 3)[3]

    else:
        print("\n\tRun like: ./fileget.py -n <nameserver> -f <surl>\n")
        exit(1)
    
else:
    print("\n\tRun like: ./fileget.py -n <nameserver> -f <surl>\n")
    exit(1)

# UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
s.settimeout(5) # timeout in case nameserver doesn't respond

send_data_UDP = "WHEREIS "+server

try:
    # sending WHEREIS <fileserver> to nameserver
    s.sendto(send_data_UDP.encode('utf-8'), (ip, port))
except:
    print("\n\tCouldn't establish connection with the nameserver.\n")
    s.close()
    exit(1)

try:
    # waiting for the response
    data_UDP, address = s.recvfrom(1024)
except:
    print("\n\tConnection to the nameserver timed out with no response.\n")
    s.close()
    exit(1)

# close the packet
s.close()

# TCP
filename_list = []

# if GET ALL start asking for index
if filename_init == '*':
    filename_list.append("index")
else:
    filename_list.append(filename_init)

# ask for one file or more in case of GET ALL
for filename in filename_list:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # establish connection to the fileserver
        s.connect((data_UDP.decode('utf-8').split(" ")[1].split(":")[0], int(data_UDP.decode('utf-8').split(":")[1])))
    except:
        print("\n\tFileserver not found.\n")
        s.close()
        exit(1)

    # request file and authorize
    send_data_TCP = "GET "+filename+" FSP/1.0\r\n"
    s.send(send_data_TCP.encode('utf-8'))
    send_data_TCP = "Hostname: "+server+"\r\n"
    s.send(send_data_TCP.encode('utf-8'))
    send_data_TCP = "Agent: xmlkvy00\r\n\r\n"
    s.send(send_data_TCP.encode('utf-8'))

    data_TCP = b''

    # wait for data stream and concatenate them together until there is nothing comming throught buffer
    while True:
        buff, address = s.recvfrom(1024)
        data_TCP = data_TCP + buff
        if buff == b'':
            break

    # split data packet to its header and content (get the return code out of the header to the msg)
    header = data_TCP.split(b"\r\n\r\n",1)[0]
    content = data_TCP.split(b"\r\n\r\n",1)[1]
    msg = header.split(b" ",1)[1].split(b"\r\n",1)[0].decode('utf-8')

    # write progress to stdout
    if not filename == "index":
        print("\n  Getting:  "+filename+"\t\t...........................\t"+msg)
    else:
        print("\n  index:\n          "+re.sub('\n',"\n          ",content.decode('utf-8')))

    # if GET ALL mode is active get all of the filenames from index content to list
    if filename_init == "*" and filename == "index":
        for piece in content.decode('utf-8').split("\r\n"):
            if not piece == "":
                filename_list.append(piece)

    # when download was successful try to construct original path to the file from the filename if there is any
    if msg == "Success" and not filename == "index":
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except:
                pass
        
        # write the downloaded file content to a new file of the same name
        f = open(filename, "wb")
        f.write(content)
        f.close

    # close the packet
    s.close()
print("\n")