from client import *
from server import *
from header import *
from application import *
import time
import sys
import os


# Three way handshake
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
        print('Did not receive SYN ACK: Connection timeout')
        client_socket.close()
        sys.exit()


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
            print('Did not receive ACK from client. Server closing.')
            server_socket.close()
            sys.exit

def read_header(data):
    header_from_data = data[:12]
    seq, ack, flags, win = parse_header (header_from_data)
    return seq, ack, flags

# This function handles the finishing part of the client
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
                print(f'A winner is you. Du har mottatt en ACK')

                # Exiting the loop
                break
        # If no response packet is received, it will resend the FIN packet
        except:
            # Resending the FIN packet to the client
            client_socket.send(FIN_packet)

    # Closes the socket connection with the client
    client_socket.close()
    print(f'Closing client gracefully')

    # Exiting the prosess
    sys.exit()

# Gracefully close when the transfer is finished
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