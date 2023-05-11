from client import *
from server import *
from header import *
from application import *
import time
import sys
import os

# TO DO: Sjekke at ACK kommer frem, legg inn en timer

# Three way handshake
def handshake_client(client_socket):
    # Client starter med å sende SYN
    SYN_packet = create_packet(0, 0, 8, 64000, b'')
    client_socket.send(SYN_packet)
    print('The client initiates the handshake by sending SYN')

    client_socket.settimeout(0.5) # Sjekk om tiden skal være like lang her
    
    try: 
        # Client mottar data fra server
        data = client_socket.recvfrom(1472)[0]
        
        while data:
            # Sjekke pakkens header
            seq, ack, flags = read_header(data)

            # Hvis header har aktivert SYN-ACK flagg
            if flags == 12:
                ACK_packet = create_packet(0, 0, 4, 64000, b'')
                client_socket.send(ACK_packet)
                
                print('The client has received a SYNACK. Ending the handshake from their end by sending an ACK to the server')

                return
            
    except:
        print('Did not receive SYN ACK: Connection timeout')
        client_socket.close()
        sys.exit()


def handshake_server(flags, server_socket, address):
    # Sjekker om vi har mottatt SYN-flagg fra client
    if flags == 8:
        print('The server has received a SYN. Replying with a SYNACK')

        # Lager en SYN ACK pakke
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)

        server_socket.settimeout(0.5)

        try:
            data = server_socket.recvfrom(1472)[0]
            if data:
                
                header_from_data = data[:12]
                seq, ack, flags, win = parse_header(header_from_data)

                if flags == 4:
                    # Server mottar ACK fra klient og er da klar for å motta datapakker
                    print('The server received an ACK from client. Handshake complete')
                    server_socket.settimeout(None)
                    return True
        except:
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

def close_server(server_socket, address):
    # Creating a ACK packet
    ACK_packet = create_packet(0, 0, 4, 64000, b'')

    # Sending the ACK packet back to the client
    server_socket.sendto(ACK_packet, address)
    print(f'Sending ACK to client.')

    # Closes the socket connection with the server
    server_socket.close()
    print(f'Closing serveren gracefully')

    # Exiting the prosess
    sys.exit()

# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements