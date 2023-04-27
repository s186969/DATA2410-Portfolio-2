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

    # Establish reliable connection with handshake
    handshake = handshake_client(client_socket)

    seq = 1
    ack = 0

    # Sende data ved å bruke stop and wait
    if args.reliablemethod == 'saw':
        stop_and_wait(client_socket, file_name, seq, ack)

    # Sende data ved å bruke Go back N
    elif args.reliablemethod == 'gbn':
        go_back_N(client_socket, file_name)

    # elif args.reliablemethod == 'sr':

    # Denne kan vi nok ta bort når vi er ferdige
    else:
        send_data(client_socket, file_name)

def stop_and_wait(client_socket, file_name, seq_client, ack_client):
    # Holde kontroll på data sendt
    number_of_data_sent = 0

    # Leser bildet oslomet.jpg og sender dette til server
    with open(file_name, 'rb') as f:
        image_data = f.read()

    # Så lenge vi ikke har sendt hele bildet, fortsetter vi å sende
    while number_of_data_sent < len(image_data):

        # Må hente ut riktige 1460 bytes av arrayet med image-data
        image_data_start = number_of_data_sent
        image_data_stop = image_data_start + 1460
        data = image_data[image_data_start: image_data_stop]

        # Bruker metode fra header.py til å lage pakke med header og data
        packet = create_packet(seq_client, ack_client, 0, 64000, data)

        # Dette kan vi bruke når vi skal ha packet loss
        #if seq_client == 2:
        #    print("Sender ikke pakke nummer 2")
        #    number_of_data_sent = number_of_data_sent
        #    seq_client += 1
        #else:
        print(f'Sender pakke med seq: {seq_client}')
        client_socket.send(packet)

        # Venter på ack fra server
        client_socket.settimeout(0.5)

        # Variabel for å sjekke om man har mottatt to akc på samme pakke
        nack = 0 
        try:
            receive = client_socket.recv(1472)
            seq, ack, flags = read_header(receive)
            print(f'Mottatt pakke med ack: {ack}')
            if ack == seq_client:
                nack += 1
                if nack > 1: # Sjekke om mottatt to ack på samme pakke
                    number_of_data_sent = number_of_data_sent
                    # Pakken må sendes på nytt
                else:
                    number_of_data_sent += len(data)
                    seq_client += 1
            
        except:
            number_of_data_sent = number_of_data_sent
            # Pakken må sendes på nytt

    # Sende et FIN flagg for å avslutte
    FIN_packet = create_packet(0, 0, 2, 64000, b'')
    client_socket.send(FIN_packet)
    print('Nå har clienten sendt FIN - sending ferdig')

    sys.exit()

# Go-Back-N():
# Sender 5 pakker samtidig
# venter på ack innenfor en tid på 500ms
# hvis ikke ack er mottatt, må alle pakker som er sendt
# i vinduet sendes på nytt.

def go_back_N(client_socket, file_name):
    sender_window = [1,2,3]
    number_of_data_sent = 0
    print(f'Antall data sendt: {number_of_data_sent}') #debug

    # Leser bildet og sender dette til server
    with open(file_name, 'rb') as f:
        image_data = f.read()
    print('Bildet har en størrelse på: ', len(image_data)) #debug

    while number_of_data_sent < len(image_data):
        # loop_data_sent hjelper slik at ikke for-løkken sender den samme pakken tre ganger
        loop_data_sent = number_of_data_sent

        #for løkke som sender en pakke per indeks i sender_window, setter seq lik index i arrayet
        for i in sender_window:
            image_data_start = loop_data_sent
            image_data_stop = image_data_start + 1460
            data = image_data[image_data_start: image_data_stop]

            #Opprette pakke og sende den
            packet = create_packet(i,0,0,64000,data)
            client_socket.send(packet)
            print(f'Sendt pakke nummer {i}, med størrelse {len(data)}')

            #Oppdatere verdier for data sent både lokalt i for løkke og globalt i while løkke
            loop_data_sent += len(data)
            number_of_data_sent += len(data)
        
        #Timer, denne skal vel egentlig komme etter hver enkelt pakke?
        client_socket.settimeout(0.5)

        try:
            packet_count = 0
            for i in sender_window:
                receive = client_socket.recv(1472)
                seq, ack, flags = read_header(receive)
                print(f'Mottatt pakke med ack: {ack}')
                
                # Her må vi håndtere at pakker skal slettes
                # hvis de ikke kommer i rekkefølge, og hvordan
                # sender_window da oppdateres



            sender_window = [sender_window[0]+3, sender_window[1]+3, sender_window[2]+3]
            array_as_string = " ".join(str(element) for element in sender_window)
            print(array_as_string)
            print(f'Numbers of data sent: {number_of_data_sent}')
        except:
            number_of_data_sent = number_of_data_sent
            print("Mottok ikke ack innen tiden")
            # Pakken må sendes på nytt

    # Sende et FIN flagg for å avslutte
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





# selective-Repeat():
# Heller enn å slette pakker som er kommet i feil rekkefølge
# skal de buffres og settes på riktig plass.
# Bruke arrays her