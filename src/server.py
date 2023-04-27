from socket import *
from application import *
from drtp import *
from header import *

def receive_data(data, received_data):
    received_data += data[12:]
    return received_data       

def go_back_N_server(server_socket):
    last_received_seq = 0
    received_data = b''

    while True:
        # Receiving a message from a client
        tuple = server_socket.recvfrom(1472)
        data = tuple[0]
        address = tuple[1]

        # Hente ut og lese av header
        header_from_data = data[:12] 
        seq, ack, flags, win = parse_header (header_from_data)
        print(f'Pakke: {seq}, flagget: {flags}, størrelse: {len(data)}')

        if flags == 2:
            # Sjekke om pakken som er mottatt inneholder FIN-flagg
            print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
            # Når FIN flagg er mottatt skriver vi dataen til filen. 
            mengde = len(received_data)
            print(f'Received data er: {mengde}')
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)
            received_data = b''
            last_received_seq = 0

        if seq == last_received_seq + 1:
            # Oppretter en tilhørende ack-pakke ved å sette ack til å være seq
            ACK_packet = create_packet(0,seq,0,64000,b'') 

            # Sender ack-pakken til client
            server_socket.sendto(ACK_packet, address)
            received_data = receive_data(data, received_data)
            last_received_seq += 1
        
        if seq > last_received_seq:
            continue


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

        #if args.reliablemethod == 'sw':
        #    send_and_wait_server()
        while True:
            # Receiving header from a client
            tuple = server_socket.recvfrom(1472)
            data = tuple[0]
            address = tuple[1]

            header_from_data = data[:12]
            seq, ack, flags, win = parse_header(header_from_data)

            # seq, ack, flags = read_header(data)
            if seq == 0 and ack == 0:       # Skal denne være med???
                            # Hente ut og lese av header
                handshake_server(flags, server_socket, address)
                print('Handshake er gjennomført')
                if args.reliablemethod == 'saw':
                    print('sender nå til saw')
                    stop_and_wait(server_socket)
                elif args.reliablemethod == 'gbn':
                    print('sender nå til gbn')
                    go_back_N_server(server_socket)
            
            # Brukes til å håndtere pakker i forbindelse med å finne RTT
            if b'ping' in data:
                server_socket.sendto(data, address)

                    
def stop_and_wait(server_socket):
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

        if flags == 2:
            # Sjekke om pakken som er mottatt inneholder FIN-flagg
            print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
            # Når FIN flagg er mottatt skriver vi dataen til filen.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)
            received_data = b''

        # Hvis seq er større enn null har vi mottatt en datapakke
        elif seq > 0:
            # Lagrer mottatt data i variabelen received_data vha funksjonen receive data
            received_data = receive_data(data, received_data)

            # Oppretter en tilhørende ack-pakke ved å sette ack til å være seq
            ACK_packet = create_packet(0, seq, 0, 64000, b'')

            # Sender ack-pakken til client
            server_socket.sendto(ACK_packet, address)






            
# Stop and wait
    # wait for packet
    # If packet is OK, send ACK
    # Else, send DUPACK
    # Repeat

# Go-Back-N()
    # Passes on data (lagre i en variabel?) in order.
    # Hvis pakker ankommer i feil rekkefølge indikerer dette
    # pakket loss og reordering. 
    # I dette tilfellet skal mottaker ikke sende ack og kan
    # slette pakkene som kom i feil rekkefølge

# Selective-Repeat():
    # Tror ikke det skjer så mye her, 
    # sender neste i pakkene i som ikke allerede er sendt