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

        #if args.reliablemethod == 'sw':
        #    send_and_wait_server()

        received_data = b''
        while True:
            # Pinging back to the client
            data, address = server_socket.recvfrom(1472)
            if b"PING" in data:
                server_socket.sendto(data, address)

            # Hente ut og lese av header
            header_from_data = data[:12] 
            seq, ack, flags, win = parse_header (header_from_data)
            # seq, ack, flags = read_header(data)

            # Establish connection if seq and ack is 0
            if seq == 0 and ack == 0:
                if flags != 2:
                    handshake_server(flags, server_socket, address)
                else:
                    # Sjekke om pakken som er mottatt inneholder FIN-flagg
                    print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
                    # Når FIN flagg er mottatt skriver vi dataen til filen. 
                    with open(file_name, 'wb') as f:
                        f.write(received_data)
                        print(f'HER ER DET VI HAR FÅTT: {received_data}')

            # Hvis seq er større enn null har vi mottatt en datapakke
            elif seq > 0:
                # Lagrer mottatt data i variabelen received_data vha funksjonen receive data
                received_data = receive_data(data, received_data)

                # Oppretter en tilhørende ack-pakke ved å sette ack til å være seq
                ACK_packet = create_packet(0,seq,0,64000,b'') 

                # Sender ack-pakken til client
                server_socket.sendto(ACK_packet, address)

                print('Her sendes en ack-pakke')

            ''' KAN SANNSYNLIGVIS TAS BORT, er håndtert over her. Under if seq == 0 and ack == 0...
            # Sjekke om pakken som er mottatt inneholder FIN-flagg
            elif flags == 2:
                print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
                # Når FIN flagg er mottatt skriver vi dataen til filen. 
                with open("received_image.jpg", 'wb') as f:
                    f.write(received_data)
                    print(f'HER ER DET VI HAR FÅTT: {received_data}')

            # Funksjon for å oppdatere received_data
            else:
                received_data = receive_data(data, received_data)
            '''
            
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