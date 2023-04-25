from application import *
from drtp import *
from header import *
from socket import *

# Starte en klient
def start_client(args):
    # Defining the IP address using the '-I' flag
    ip_address = args.serverip

    # Defining the port number using the '-p' flag
    port_number = args.port

    # Create a UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.connect((ip_address, port_number))

    handshake = handshake_client(client_socket)

    send_data(client_socket)

def send_data(client_socket):
    with open('oslomet.jpg', 'rb') as f: #FLAGG
        image_data = f.read()
        data_length = len(image_data)
        print(f'Størrelsen til bildet er: {data_length}')
    client_socket.send(image_data)

# En funksjon for å lage datapakker med header?

# En funksjon for å sende datapakker

# En funksjon for å motta data (ack)
    # Hvis en pakke ikke inneholder noe data, så er den en "ACK")

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