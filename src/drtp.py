from client import *
from server import *
from header import *
from application import *
import time

# This function calculates the average round trip time of 20 transfers where a transfer consists of 1472 bytes
def round_trip_time(client_socket, ip_address, port_number):
    # Creates a message of 1460 bytes to be sent in the packet 
    ping = b'ping' + (b'0' * 1456)
    
    # Creates a packet with a header and the message
    # Kommentere hvorfor vi har 1,1 her. Kanskje endre? 
    packet = create_packet(1,1,0,64000, ping)

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

                # Et annet forslag. Må fjerne de øvrige linjene
                # Substracting the round that failed
                # round = round - 1
                
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
        print('Connection timeout')
        # Skal vi sende en ny SYN??? (Gå opp til :
        # client_socket.send(SYN_packet)    ??


def handshake_server(flags, server_socket, address):
    # Sjekker om vi har mottatt SYN-flagg fra client
    if flags == 8:
        # Lager en SYN ACK pakke
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)
        print('Nå har server sendt SYN ACK')
    
    if flags == 4:
        # Server mottar ACK fra klient og er da klar for å motta datapakker
        return
        
def read_header(data):
    header_from_data = data[:12]
    seq, ack, flags, win = parse_header (header_from_data)
    return seq, ack, flags


# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements
