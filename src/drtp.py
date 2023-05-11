# Description:
# Imports the necessary libraries
# client: This module contains the client functions.
# server: This module contains the server functions.
# header: This module contains the functions for creating and reading the header.
# application: This module contains the application layer functions.
# time: This module provides various time-related functions.
# sys: This module provides access to some variables used or maintained by the interpreter and to functions that interact strongly with the interpreter.
# os: This module provides a portable way of using operating system dependent functionality.

from client import *
from server import *
from header import *
from application import *
import time
import sys
import os

# Description:
# This function implements the client-side of the three-way handshake process. The client initiates the handshake by sending a SYN packet, and then waits for a SYN-ACK packet from the server. Upon receiving the SYN-ACK, the client sends an ACK packet to complete the handshake process.
# Arguments: 
# client_socket: The socket object for the client.
# Returns: None
def handshake_client(client_socket):
    # Client starts by sending SYN
    SYN_packet = create_packet(0, 0, 8, 64000, b'')
    client_socket.send(SYN_packet)
    print('The client initiates the handshake by sending SYN')

    # Set a timeout
    client_socket.settimeout(0.5)
    
    try: 
        # Client receives data from the server
        data = client_socket.recvfrom(1472)[0]
        
        while data:
            # Check the packet's header
            seq, ack, flags = read_header(data)

            # If the header has activated the SYN-ACK flag, the client sends the last part of the handshake: The ACK
            if flags == 12:
                ACK_packet = create_packet(0, 0, 4, 64000, b'')
                client_socket.send(ACK_packet)
                
                print('The client has received a SYN ACK. Ending the handshake from their end by sending an ACK to the server')
                return
            
    # If the client didn't receive a SYN ACK, it closes the connection.
    except:
        # Print error message
        print('Did not receive SYN ACK: Connection timeout')
        client_socket.close()
        sys.exit()

# Description:
# This function implements the server-side of the three-way handshake process. The server checks if it has received a SYN packet from the client. If it has, the server sends a SYN-ACK packet in response. The server then waits for an ACK packet from the client. If it receives the ACK, the handshake is considered complete, and the server is ready to receive data.
# Arguments: 
# flags: The flags value from the received packet's header.
# server_socket: The socket object for the server to send and receive data.
# address: The address of the client.
# Returns:
# bool: True if the handshake is complete, otherwise False.
def handshake_server(flags, server_socket, address):
    # Check if we have received SYN flag from the client
    if flags == 8:
        print('The server has received a SYN. Replying with a SYNACK')

        # Creating a SYN ACK packet
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)

        server_socket.settimeout(0.5)
        # Receive and exctract data from the client
        try:
            data = server_socket.recvfrom(1472)[0]
            if data:
                
                header_from_data = data[:12]
                seq, ack, flags, win = parse_header(header_from_data)

                if flags == 4:
                    # The server receives an ACK from the client and is ready to receive the data
                    print('The server received an ACK from client. Handshake complete')
                    server_socket.settimeout(None)
                    return True
        # If the server doesn't receive an ACK from the client, it will close.
        except:
            return False

# Description:
# This function reads the header from a given data packet and extracts the sequence number, acknowledgment number, and flags from it using the parse_header() function.
# Arguments: 
# data: The data packet to read the header from.
# Returns:
# seq: The sequence number from the header.
# ack: The acknowledgment number from the header.
# flags: The flags value from the header.
def read_header(data):
    # Extracting the header from the data
    header_from_data = data[:12]
    # Extracting the sequence number, acknowledgment number, and flags from the header
    seq, ack, flags, win = parse_header (header_from_data)
    return seq, ack, flags


# Description:
# This function closes the client-side connection by sending a FIN packet and waiting for an ACK packet in response. If no response is received within the specified timeout, the FIN packet is resent. Once the ACK packet is received, the client socket is closed gracefully.
# Arguments: 
# client_socket: The socket object for the client to send and receive data.
# Returns: None
def close_client(client_socket):
    # Creates a FIN packet
    FIN_packet = create_packet(0, 0, 2, 64000, b'')

    # Sending the FIN packet to the client
    client_socket.send(FIN_packet)
    print('Client sent FIN - sending over')

    # Sets a timeout
    client_socket.settimeout(0.5)

    # While waiting for the response
    while True:
        try:
            print("Waiting for 'FIN' to be ACKed")
            
            # Receiving the response packet
            data, address = client_socket.recvfrom(1472)

            # Extracting the data from the header
            seq, ack, flags = read_header(data)

            # Breaking the loop if it is an ACK packet
            if flags == 4:
                print(f'A winner is you. You have received an ACK')

                # Exiting the loop
                break
        # If no response packet is received, it will resend the FIN packet
        except:
            # Resending the FIN packet to the client
            client_socket.send(FIN_packet)

    # # Gracefully close when the transfer is finished
    client_socket.close()
    print(f'Closing client gracefully')

    # Exiting the prosess
    sys.exit()


# Description:
# This function closes the server-side connection by sending an ACK packet in response to the client's FIN packet. After sending the ACK packet, the server socket is closed gracefully.
# Arguments: 
# server_socket: The socket object for the server to send and receive data.
# address: The address of the client.
# Returns: None
def close_server(server_socket, address):
    # Creating a ACK packet
    ACK_packet = create_packet(0, 0, 4, 64000, b'')

    # Sending the ACK packet back to the client
    server_socket.sendto(ACK_packet, address)
    print(f'Sending ACK to client.')

    # Closes the socket connection with the server
    server_socket.close()
    print(f'Closing the server gracefully')

    # Exiting the prosess
    sys.exit()