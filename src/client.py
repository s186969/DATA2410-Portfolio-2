from application import *
from drtp import *
from header import *
from socket import *
import sys

# Starte en klient
def start_client(args):
    # Defining the IP address using the '-i' flag
    ip_address = args.serverip

    # Defining the port number using the '-p' flag
    port_number = args.port

    # Defining the file name using the '-f' flag
    file_name = args.filename

    # Create a UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.connect((ip_address, port_number))

    handshake = handshake_client(client_socket)

    seq = 1
    ack = 0

    if args.reliablemethod == 'saw':
        send_and_wait(client_socket, file_name, seq, ack)

    # elif args.reliablemethod == 'gbn':

    elif args.reliablemethod == 'sr':
        selective_repeat(client_socket, file_name, seq, ack)

    else:
        send_data(client_socket, file_name)

def selective_repeat(client_socket, file_name, seq_client, ack_client):
    # Set up variables
    window_size = 5
    window_start = seq_client
    window_end = window_start + window_size
    data_sent = (seq_client - 1) * 1460
    packets_in_buffer = {}
    last_ack_received = seq_client - 1

    # Read file and send packets
    with open(file_name, 'rb') as f:
        image_data = f.read()
        data_length = len(image_data)

        while data_sent < data_length:
            # Send packets in window
            for seq_client in range(window_start, window_end):
                if seq_client not in packets_in_buffer:
                    # Get data for packet
                    packet_start = (seq_client - 1) * 1460
                    packet_stop = min(packet_start + 1460, data_length)
                    data = image_data[packet_start:packet_stop]

                    # Create packet and send
                    packet = create_packet(seq_client, ack_client, 0, 64000, data)
                    client_socket.send(packet)
                    print('Sending packet:', seq_client)

                    # Add packet to buffer
                    packets_in_buffer[seq_client] = data

            # Wait for acks and handle them
            try:
                client_socket.settimeout(0.5)
                receive = client_socket.recv(1472)
                seq, ack, flags = read_header(receive)
                print('Received ack:', ack)

                # Update window and buffer
                if ack > last_ack_received:
                    num_acks_received = ack - last_ack_received
                    for i in range(num_acks_received):
                        # Remove packet from buffer
                        packets_in_buffer.pop(window_start + i)

                    # Update window
                    last_ack_received = ack
                    window_start = last_ack_received + 1
                    window_end = window_start + window_size

                    # Update data sent
                    data_sent = last_ack_received * 1460
            except:
                # Resend packets not acknowledged
                for seq_client, data in packets_in_buffer.items():
                    packet = create_packet(seq_client, ack_client, 0, 64000, data)
                    client_socket.send(packet)
                    print('Resending packet:', seq_client)

    # Send FIN packet
    FIN_packet = create_packet(0, 0, 2, 64000, b'')
    client_socket.send(FIN_packet)
    print('Sending FIN packet')

    # Close socket and exit
    client_socket.close()
    sys.exit()




def send_and_wait(client_socket, file_name, seq_client, ack_client):
    number_of_data_sent = 0

    # Leser bildet oslomet.jpg og sender dette til server
    with open(file_name, 'rb') as f:
        image_data = f.read()
        data_length = len(image_data)  # debug

    while number_of_data_sent < len(image_data):

        # Må hente ut riktige 1460 bytes av arrayet med image-data
        image_data_start = number_of_data_sent
        image_data_stop = image_data_start + 1460
        data = image_data[image_data_start: image_data_stop]

        # Bruker metode fra header.py til å lage pakke med header og data
        packet = create_packet(seq_client, ack_client, 0, 64000, data)
        client_socket.send(packet)
        print('Her sendes en datapakke')

        # Venter på ack fra server
        client_socket.settimeout(0.5)
        try:
            receive = client_socket.recv(1472)
            seq, ack, flags = read_header(receive)
            if ack == seq_client:
                number_of_data_sent += len(data)
                seq_client += 1
        except:
            number_of_data_sent = number_of_data_sent
            # Pakken må sendes på nytt

    # Sende et FIN flagg
    FIN_packet = create_packet(0, 0, 2, 64000, b'')
    client_socket.send(FIN_packet)
    print('Nå har clienten sendt FIN - sending ferdig')

    sys.exit()


def send_data(client_socket, file_name):
    # Leser bildet oslomet.jpg og sender dette til server
    with open(file_name, 'rb') as f:
        image_data = f.read()
        data_length = len(image_data)  # debug
        # print(f'Størrelsen til bildet er: {data_length}') #debug

    # En funksjon for å lage datapakker med header
    seq = 1
    ack = 0
    number_of_data_sent = 0

    while number_of_data_sent < len(image_data):
        # print(f'Number of data sent: {number_of_data_sent}')
        # print("Lengden til image_data", len(image_data))

        # Må hente ut riktige 1460 bytes av arrayet med image-data
        image_data_start = number_of_data_sent
        image_data_stop = image_data_start + 1460
        data = image_data[image_data_start: image_data_stop]

        # Bruker metode fra header.py til å lage pakke med header og data
        packet = create_packet(seq, ack, 0, 64000, data)
        # print(packet)

        # Sender datapakken
        client_socket.send(packet)

        # Sequence number må økes med en, og number of data sent må oppdateres
        number_of_data_sent += len(data)
        seq += 1
        print(f'Antall bytes sent: {number_of_data_sent}')

    # Sende et FIN flagg
    FIN_packet = create_packet(0, 0, 2, 64000, b'')
    client_socket.send(FIN_packet)
    print('Nå har clienten sendt FIN - sending ferdig')

    sys.exit()

# Stop and wait funksjon:
# sender pakke og venter på ack fra server
# sender en ny pakke når ack er mottatt
# hvis ack uteblir skal man vente i 500 ms og deretter sende pakken på nytt
# hvis man mottar to ack så sender man pakken på nytt

# Go-Back-N():
# Sender 5 pakker samtidig
# venter på ack innenfor en tid på 500ms
# hvis ikke ack er mottatt, må alle pakker som er sendt
# i vinduet sendes på nytt.

# selective-Repeat():
# Heller enn å slette pakker som er kommet i feil rekkefølge
# skal de buffres og settes på riktig plass.
# Bruke arrays her