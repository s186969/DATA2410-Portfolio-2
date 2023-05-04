from client import *
from server import *
from header import *
from application import *
import time
import sys

# This function calculates the average round trip time of 20 transfers where a transfer consists of 1472 bytes
def round_trip_time(client_socket):
    # Creates a message of 1460 bytes to be sent in the packet 
    ping = b'ping' + (b'0' * 1456)
    
    # Creates a packet with a header and the message
    packet = create_packet(0, 0, 0, 64000, ping)

    # Initialise the round trip time 
    total_round_trip_time = 0

    # Sets the number of rounds
    round = 20

    # For each round
    for i in range(round):
        # Records the start time of the round
        start_time = time.time()

        # print(f'Sending packet {i+1}') # Debug
        
        # Sends the packet to the specified address
        client_socket.send(packet)

        # While waiting for response
        while True:
            try:
                # Sets a timeout for 0.5 seconds
                client_socket.settimeout(0.5)

                # Receiving the response packet
                pong, address = client_socket.recvfrom(1472)

                # Records the end time of the round
                end_time = time.time()

                # Calculating the round trip time by subtracting the start time from the end time
                round_trip_time = end_time - start_time

                # Adds the current round trip time to the total round trip time
                total_round_trip_time = total_round_trip_time + round_trip_time

                # print(f'Round {i+1}: {round_trip_time} s') # Debug

                # Exits the while loop after receiving the response packet in order to start next round
                break
            
            # If no response packet is received within 0.5 second, it will exit the while loop to start next round
            except:
                # Records the end time of the round
                end_time = time.time()

                # Calculating the round trip time by subtracting the start time from the end time
                round_trip_time = end_time - start_time

                # Adds the current round trip time to the total round trip time
                total_round_trip_time = total_round_trip_time + round_trip_time

                # print(f'Round {i+1}: Timeout') # Debug

                # Exits the while loop in order to start next round
                break

    # Calculating the average round trip time by dividing the total round trip time by the number of rounds
    average_round_trip_time = total_round_trip_time / round

    # print(f'Average RTT: {average_round_trip_time} s') # Debug

    # Returns the average round trip time
    return average_round_trip_time

# TO DO: Sjekke at ACK kommer frem, legg inn en timer

# Three way handshake
def handshake_client(client_socket): 
    # Client starter med å sende SYN
    SYN_packet = create_packet(0, 0, 8, 64000, b'')
    client_socket.send(SYN_packet)
    print('Her sender clienten SYN')

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
                print('Nå har clienten sendt ACK')
                return
            
    except:
        print('Did not receive SYN ACK: Connection timeout')
        client_socket.close()
        sys.exit()


def handshake_server(flags, server_socket, address):
    # Sjekker om vi har mottatt SYN-flagg fra client
    if flags == 8:
        # Lager en SYN ACK pakke
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)
        print('Nå har server sendt SYN ACK')

        server_socket.settimeout(0.5)

        try:
            data = server_socket.recvfrom(1472)[0]
            if data:
                
                header_from_data = data[:12]
                seq, ack, flags, win = parse_header(header_from_data)

                #server_socket.settimeout(0.5)
                if flags == 4:
                    # Server mottar ACK fra klient og er da klar for å motta datapakker
                    print('Received ACK from client. Handshake done. Ready to receive.')
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
    print('Nå har clienten sendt FIN - sending ferdig')

    # Sets a timeout
    client_socket.settimeout(0.5)

    # While waiting for the response
    while True:
        try:
            print("Venter på pakke 'FIN sin' ACK")
            
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
    print(f'Avslutter klienten grasiøst')

    # Exiting the prosess
    sys.exit()

def close_server(server_socket, address):
    # Creating a ACK packet
    ACK_packet = create_packet(0, 0, 4, 64000, b'')

    # Sending the ACK packet back to the client
    server_socket.sendto(ACK_packet, address)
    print(f'Sender ACK til klient.')

    # Closes the socket connection with the server
    server_socket.close()
    print(f'Avslutter serveren grasiøst')

    # Exiting the prosess
    sys.exit()

# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements