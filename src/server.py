from socket import *
from application import *
from drtp import *
from header import *

def receive_data(data, file_name):
    # Skriver data mottatt til filen received_image.jpg
    with open(file_name, 'wb') as f:
        f.write(data)

def start_server(args):
    # Defining the IP address using the '-b' flag
    ip_address = args.bind
    
    # Defining the port number using the '-p' flag
    port_number = args.port

    # Defining the file name using the '-f' flag
    file_name = args.filename
    
    # Creates a UDP socket
    with socket(AF_INET, SOCK_DGRAM) as server_socket:

        # Bind socket to the server
        server_socket.bind((ip_address, port_number))

        # Prints a message that the server is ready to receive
        print(f"The server is ready to receive")

        while True:
            # Receiving a message from a client
            tuple = server_socket.recvfrom(1472)
            data = tuple[0]
            address = tuple[1]

            # Sjekke pakkens header
            seq, ack, flags = read_header(data)

            # Establish connection if seq and ack is 0
            if seq == 0 and ack == 0:
                handshake_server(flags, server_socket, address)
            
            # Herfra er mottak av data
            receive_data(data, file_name)
  


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