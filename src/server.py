from socket import *
from application import *
from drtp import *
from header import *


def receive_data(data, received_data):
    received_data += data[12:]
    return received_data


def start_server(args):
    # Defining the IP address using the '-i' flag
    ip_address = args.serverip

    # Defining the port number using the '-p' flag
    port_number = args.port

    # Creates a UDP socket
    with socket(AF_INET, SOCK_DGRAM) as server_socket:

        # Bind socket to the server
        server_socket.bind((ip_address, port_number))

        # Prints a message that the server is ready to receive
        print(f"The server is ready to receive")

        # if args.reliablemethod == 'sw':
        #    send_and_wait_server()
        while True:
            # Receiving header from a client
            # data, address = server_socket.recvfrom(1472) # Forslag til å erstatte de tre linjene under
            tuple = server_socket.recvfrom(1472)
            data = tuple[0]
            address = tuple[1]

            header_from_data = data[:12]
            seq, ack, flags, win = parse_header(header_from_data)

            # Used to calculate RTT. Checks if the received data is a ping.
            if b'ping' in data:
                # If ping is found, it will pong back to the sender
                server_socket.sendto(data, address)

                # Continues to the next iteration of the while loop
                continue

            # seq, ack, flags = read_header(data)
            # Hente ut og lese av header

            handshake = handshake_server(flags, server_socket, address)
            print('Handshake er gjennomført')

            if args.reliablemethod == 'saw':
                print('sender nå til saw')
                stop_and_wait(server_socket, args)
            elif args.reliablemethod == 'gbn':
                print('sender nå til gbn')
                go_back_N_server(server_socket, args)
            elif args.reliablemethod == 'sr':
                print('sender nå til sr')
                sel_rep_server(server_socket, args)


def stop_and_wait(server_socket, args):
    received_data = b''
    while True:
        # Receiving a message from a client
        tuple = server_socket.recvfrom(1472)
        data = tuple[0]
        address = tuple[1]

        # Hente ut og lese av header
        header_from_data = data[:12]
        seq, ack, flags, win = parse_header(header_from_data)
        # seq, ack, flags = read_header(data)

        # Test case skip ack: The server ommits sending ack, so client has to resend
        if args.testcase == 'skip_ack' and seq == 2:
            print('Ack for seq 2 blir nå skippet')
            args.testcase = None
            print(f'args.testcase = {args.testcase}')
            continue

        if flags == 2:
            # Sjekke om pakken som er mottatt inneholder FIN-flagg
            print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
            # Når FIN flagg er mottatt skriver vi dataen til filen.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)

            # Closing the connection gracefully
            close_server(server_socket, address)

        # Hvis seq er større enn null har vi mottatt en datapakke
        elif seq > 0:
            # Lagrer mottatt data i variabelen received_data vha funksjonen receive data
            received_data = receive_data(data, received_data)

            # Oppretter en tilhørende ack-pakke ved å sette ack til å være seq
            ACK_packet = create_packet(0, seq, 0, 64000, b'')

            # Sender ack-pakken til client
            server_socket.sendto(ACK_packet, address)

# Stores packets that arrive in sequence. Sends an ack back to the client for each package that arrived in order
def go_back_N_server(server_socket, args):
    #Variable to store received data in bytes
    received_data = b''
    #Variable to keep track of sequence number of last packet received
    seq_last_packet = 0

    while True:
        # Receiving a message from a client
        data, address = server_socket.recvfrom(1472)

        # Extract header from packet
        header_from_data = data[:12]
        # Read sequence number and flags from header
        seq, ack, flags, win = parse_header(header_from_data)
        print(f'Pakke: {seq} received')

        # Check if flag is 2 (FIN flag enabled)
        if flags == 2:
            print('Received FIN flag from client')
            # finds the size of the amount of data received
            mengde = len(received_data)
            print(f'Received data is: {mengde} bytes')
            # When the FIN flag is received, we write the received bytes to the file.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)

            # Closing the connection gracefully
            close_server(server_socket, address)

        # check if the package we have received is the next in order
        if seq == seq_last_packet + 1:
            # Check if testcase skip_ack is enabled
            if args.testcase == 'skip_ack' and seq == 4:
                print('Does not send ACK')
                # Disable test case so that the packet can retransmit
                args.testcase = None
                continue
            else:
                # Creates an associated ack packet by setting ack to be seq
                ACK_packet = create_packet(0, seq, 0, 64000, b'')

                # Sending ack-packet to client
                server_socket.sendto(ACK_packet, address)
                # Put the package's data into the received_data variable
                received_data = receive_data(data, received_data)
                # Update sequence number of last reveived packet
                seq_last_packet = seq
        else:
            print(f'Packet {seq} received in the wrong order')
            continue

def sel_rep_server(server_socket, args):
    # Initialiserer en tom ordbok (dictionary) kalt 'buffer' for å holde pakker som kommer i feil rekkefølge.
    buffer = {}
    # Initialiserer en tom byte-streng kalt 'received_data' for å holde den mottatte dataen.
    received_data = b''
    # Initialiserer en variabel 'seq_last_packet' for å holde sekvensnummeret til den sist mottatte pakken.
    seq_last_packet = 0

    # Starter en evig løkke for å motta pakker fra klienten.
    while True:
        # Mottar data og adresse fra klienten ved hjelp av server_socket.
        data, address = server_socket.recvfrom(1472)
        # Henter headerinformasjonen fra den mottatte dataen.
        header_from_data = data[:12]
        # Parser headerinformasjonen for å hente sekvensnummeret, ACK-nummeret, flaggene og vindusstørrelsen.
        seq, ack, flags, win = parse_header(header_from_data)
        # Skriver ut informasjon om den mottatte pakken.
        print(f'Pakke: {seq}, flagget: {flags}, størrelse: {len(data)}')

        # Sjekker om mottatt pakke har FIN-flagget satt (flags == 2).
        if flags == 2:
            # Skriver ut informasjon om at FIN-flagget er mottatt og ingen flere data vil bli mottatt.
            print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
            # Skriver ut lengden på den mottatte dataen.
            print(f'Received data er: {len(received_data)}')
            # Skriver den mottatte dataen til en fil kalt 'received_image.jpg'.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)
            # Avslutter evig løkke og avslutter funksjonen.
            # break
            

        # Sjekker om sekvensnummeret til den mottatte pakken er en mer enn sekvensnummeret til den sist mottatte pakken.
        if seq == seq_last_packet + 1:
            # Håndterer et testcase hvor serveren skal hoppe over å sende en ACK for pakke med sekvensnummer 42.
            if args.testcase == 'skip_ack' and seq == 4:
                print('Sender ikke ack')
                args.testcase = None
            else:
                # Oppretter en ACK-pakke for den mottatte pakken og sender den til klienten.
                ACK_packet = create_packet(0, seq, 0, 64000, b'')
                server_socket.sendto(ACK_packet, address)
                print(f'Sender ack: {seq}')
                # Legger til data fra den mottatte pakken i 'received_data'.
                received_data = receive_data(data, received_data)
                # Oppdaterer sekvensnummeret til den sist mottatte pakken.
                seq_last_packet = seq
                # Hvis det er pakker i bufferet med sekvensnummeret en mer enn den sist mottatte pakken, behandles de og fjernes fra bufferet
                array_as_string = " ".join(str(element) for element in buffer)
                print(f'Buffer: {array_as_string}')
                while seq_last_packet + 1 in buffer:
                    seq_last_packet += 1
                    received_data = receive_data(
                        buffer[seq_last_packet], received_data)
                    del buffer[seq_last_packet]
                array_as_string = " ".join(str(element) for element in buffer)
                print(f'Buffer: {array_as_string}')
                    
        # Hvis den mottatte pakken har et annet sekvensnummer enn 0 og ikke er en etter den sist mottatte pakken, lagres den i bufferet og en ACK sendes til klienten.
        elif seq != 0:
            print('Pakken kom i feil rekkefølge, lagrer i buffer og sender ack')
            buffer[seq] = data
            ACK_packet = create_packet(0, seq, 0, 64000, b'')
            server_socket.sendto(ACK_packet, address)
