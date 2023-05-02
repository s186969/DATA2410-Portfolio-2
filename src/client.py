import time
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

    # Calculating four times round-trip time
    four_round_trip_time = 4 * round_trip_time(client_socket)
    print(f'4RTT: {four_round_trip_time} s')

    # Establish reliable connection with handshake
    handshake_client(client_socket)

    seq = 1
    ack = 0

    # Sende data ved å bruke stop and wait
    if args.reliablemethod == 'saw':
        stop_and_wait(client_socket, file_name, seq, ack, args.testcase)

    # Sende data ved å bruke Go back N
    elif args.reliablemethod == 'gbn':
        go_back_N(client_socket, file_name, args.testcase, args.windowsize)

    # Sende data ved å bruke Selective Repeat
    elif args.reliablemethod == 'sr':
        sel_rep(client_socket, file_name, args.testcase, args.windowsize)

    # Denne kan vi nok ta bort når vi er ferdige
    else:
        send_data(client_socket, file_name)

def stop_and_wait(client_socket, file_name, seq_client, ack_client, testcase):
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

        if testcase == 'loss' and seq_client == 4:
            print('Seq 4 blir nå skippet')
            testcase = None
            print(f'args.testcase = {testcase}')
            continue

        print(f'Sender pakke med seq: {seq_client}')
        client_socket.send(packet)

        # Venter på ack fra server
        client_socket.settimeout(0.5)

        # Variabel for å sjekke om man har mottatt to akc på samme pakke
        dupack = 0 
        try:
            receive = client_socket.recv(1472)
            seq, ack, flags = read_header(receive)
            print(f'Mottatt pakke med ack: {ack}')
            if ack == seq_client:
                dupack += 1
                # Sjekke om mottatt to ack på samme pakke
                if dupack > 1: 
                    continue
                    # Pakken må sendes på nytt
                else:
                    number_of_data_sent += len(data)
                    seq_client += 1
            else:
                continue
        except:
            number_of_data_sent = number_of_data_sent
            # Pakken må sendes på nytt

    # Closes the connection gracefully
    close_client(client_socket)

# Go-Back-N():
# Sender 5 pakker samtidig
# venter på ack innenfor en tid på 500ms
# hvis ikke ack er mottatt, må alle pakker som er sendt
# i vinduet sendes på nytt.

def go_back_N(client_socket, file_name, testcase, window_size):
    
    sender_window = []
    number_of_data_sent = 0
    seq_client = 1
    last_ack = 0
    ending = False

    # Leser bildet og gjør det om til bytes
    with open(file_name, 'rb') as f:
        image_data = f.read()

    #Passer på at sender_window hele tiden er fullt
    while len(sender_window) < window_size:
   
        #Sjekke om det er plass i sender window til å sende en ny pakke
        while number_of_data_sent < len(image_data) and len(sender_window) < window_size:
            if testcase == 'loss' and seq_client == 3:
                print('Seq 3 blir nå skippet')
                sender_window.append(seq_client)
                testcase = None
                seq_client += 1
                number_of_data_sent += 1460

                # Break out of the inner loop when the window is full
                if len(sender_window) >= window_size:
                    break
            
            # Hente ut riktig område av data
            image_data_start = number_of_data_sent
            image_data_stop = image_data_start + 1460
            data = image_data[image_data_start: image_data_stop]


            #Opprette pakke og sende den
            packet = create_packet(seq_client,0,0,64000,data)
            client_socket.send(packet)
            print(f'Sendt pakke nummer {seq_client}')
            number_of_data_sent += 1460

            #Legge sendt pakke inn i sender window
            sender_window.append(seq_client)
            array_as_string = " ".join(str(element) for element in sender_window)
            print(array_as_string)
            seq_client += 1


        # Motta ack fra server så lenge det er pakker i sender_window
        if len(sender_window) > 0:
            client_socket.settimeout(0.5)
            try:
                receive = client_socket.recv(1472)
                seq, ack, flags = read_header(receive)
                print(f'Mottatt pakke med ack: {ack}')
                
                #Hvis ack er tilhørende pakke i sender_window:
                if ack in sender_window:
                    # Sjekk om ack er som foventet
                    if ack == last_ack + 1:
                        last_ack = ack  # Legg til denne linjen for å oppdatere last_ack
                        sender_window.remove(ack)
                        # Hvis sender window nå er blitt tomt, betyr det at vi er ferdige
                        if len(sender_window) == 0:
                            # Setting a variable to be used to exit the outer loop
                            ending = True

                            # Exiting the inner loop
                            break
                        
                        array_as_string = " ".join(str(element) for element in sender_window)
                        print(f'Nå er vinduet: {array_as_string}')
                        
                        #Oppdaterer last_ack variabelen
                        last_ack  = ack
                        continue
            
            #Hvis vi ikke mottar noen ack fra server, tyder det på packet loss og alt 
            #sending window må sendes på nytt
            except:
                print('Mottok ikke forventet ack')
                #Tømmer sender window
                sender_window.clear()
                
                #Sender pakken etter den forrige vi vet kom frem
                seq_client = last_ack + 1
                number_of_data_sent = 1460 * last_ack

        # If the sender window is empty, the function has exited the inner loop
        if ending == True:
            # Exiting the outer loop
            break

        #For å motta resterede ack etter siste sending
        while len(sender_window) > 0 and number_of_data_sent >= len(image_data):
            client_socket.settimeout(0.5)
            try:
                receive = client_socket.recv(1472)
                seq, ack, flags = read_header(receive)
                print(f'Mottatt pakke med ack: {ack}')
                
                if ack in sender_window:
                    sender_window.remove(ack)
                    array_as_string = " ".join(str(element) for element in sender_window)
                    print(f'Nå er vinduet: {array_as_string}')
                    continue
                
            except:
                print('Noe gikk galt med å motta ack')
                sender_window.clear()
                seq_client = last_ack + 1
                print(f'Fra except her er seq_client {seq_client} forventer 4')
                number_of_data_sent = 1460 * last_ack
                continue

    # Closes the connection gracefully    
    close_client(client_socket)
        
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

# Funksjon for å sende pakker i en Selective Repeat-protokoll
# Argumenter: 
# client_socket: Socket for kommunikasjon med serveren
# file_name: Filnavn for filen som skal sendes
# testcase: Testcase for å simulere pakketap
# window_size: Størrelse på senderens vindu
def sel_rep(client_socket, file_name, testcase, window_size):

    # Funksjon for å sende en enkelt pakke gitt sekvensnummer og bilde data
    # Argumenter:
    # seq_num: Sekvensnummer for pakken som skal sendes
    # image_data: Bilde data som skal sendes
    def send_packet(seq_num, image_data):
        # Beregne startindeksen for bildedata i pakken
        image_data_start = 1460 * (seq_num - 1)
        # Beregne sluttindeksen for bildedata i pakken
        image_data_stop = image_data_start + 1460
        # Hente bildedata for denne pakken
        data = image_data[image_data_start: image_data_stop]
        # Opprette pakken med sekvensnummer og data
        packet = create_packet(seq_num, 0, 0, 64000, data)
        # Sende pakken til serveren
        client_socket.send(packet)  
        # Returnere tidspunktet pakken ble sendt
        return time.time()  

    # Initialisere variabler
    sender_window = []  # Liste over pakker i senderens vindu
    # Array med pakker som ikke har mottatt ACK, med sekvensnummer som indeks og sendetid som verdi
    unacked_packets = {}
    # Antall data sendt (i bytes)
    number_of_data_sent = 0 
    # Startsekvensnummer for klienten
    seq_client = 1  
    # Siste mottatte ACK
    last_ack = 0  
    # Retransmisjonstidsavbrudd (i sekunder)
    retransmission_timeout = 0.01  

    # Åpne filen i binærmodus og les inn bildedata
    with open(file_name, 'rb') as f: 
        # Les inn bildedata
        image_data = f.read() 

    # Hovedløkke for å sende pakker og motta ACK-er
    while True:
        # Løkke for å sende pakker til serveren
        while number_of_data_sent < len(image_data) and len(sender_window) < window_size: #
            # Hvis vi simulerer tap av pakke 4
            if testcase == 'loss' and seq_client == 4: 
                print('Følgende pakke blir ikke sendt: ', seq_client)
                # "Send pakken" og lagre tidspunktet den ble sendt
                send_time = time.time()
                # Legg til pakken i ordboken over pakker som ikke har mottatt ACK
                unacked_packets[seq_client] = send_time
                # Legg til pakken i senderens vindu
                sender_window.append(seq_client) 
                # Sett testcase til None for å ikke miste flere pakker
                testcase = None 
            else:
                # Send pakken og lagre tidspunktet den ble sendt
                send_time = send_packet(seq_client, image_data) 
                # Legg til pakken i ordboken over pakker som ikke har mottatt ACK
                unacked_packets[seq_client] = send_time 
                # Legg til pakken i senderens vindu
                sender_window.append(seq_client) 
                # Skriv ut pakkenummer som ble sendt
                print(f'Sendt pakke nummer: {seq_client}')
                # Skriv ut vinduet
                print(f'Window: [{" , ".join(map(str, sender_window))}]')

            # Oppdater sekvensnummer og antall data sendt
            seq_client += 1
            # Oppdater antall data sendt
            number_of_data_sent += 1460

        # Sjekk om noen pakker trenger å sendes på nytt på grunn av tidsavbrudd
        current_time = time.time()
        # Gå gjennom alle pakker som ikke har mottatt ACK
        for seq_num, send_time in list(unacked_packets.items()):
            # Hvis det har gått mer enn retransmission_timeout siden pakken ble sendt
            if current_time - send_time > retransmission_timeout:
                # Skriv ut pakkenummer som er resendt på grunn av tidsavbrudd
                print(f'Resender pakke nummer: {seq_num}')
                # Send pakken på nytt og lagre tidspunktet den ble sendt
                send_packet(seq_num, image_data)
                # Oppdater tidspunktet pakken ble sendt
                unacked_packets[seq_num] = current_time

        # Avslutt løkken hvis sender_window er tomt
        if not sender_window:
            break

        # Sett en tidsavbrudd for å vente på ACK fra serveren
        client_socket.settimeout(0.5)
        try:
            # Motta pakke fra serveren
            receive = client_socket.recv(1472)
            # Les headerinformasjonen fra pakken
            seq, ack, flags = read_header(receive)
            # Skriv ut ACK som er mottatt
            print(f'Mottatt pakke med ack: {ack}')

            # Hvis ACK er i senderens vindu
            if ack in sender_window:
                # Oppdater siste mottatte ACK
                last_ack = ack  
                # Fjern pakken fra senderens vindu
                sender_window.remove(ack) 
                # Fjern pakken fra listen over ikke-ACK-pakker
                unacked_packets.pop(ack, None)
        except:
            # Hvis det ikke mottas en forventet ACK
            print('Mottok ikke forventet ack')
            # Tøm senderens vindu og start sendingen fra siste mottatte ACK
            sender_window.clear()
            # Sett sekvensnummeret til å være lik siste mottatte ACK
            seq_client = last_ack + 1
            # Sett antall data sendt tilsvarende
            number_of_data_sent = 1460 * last_ack

    # Når alle pakker er sendt, send en FIN-pakke for å signalisere at sendingen er fullført
    FIN_packet = create_packet(0, 0, 2, 64000, b'')
    # Send FIN-pakken
    client_socket.send(FIN_packet)
    # Skriv ut at FIN-pakken er sendt
    print('Nå har clienten sendt FIN - sending ferdig')
    # Motta FIN-ACK fra serveren
    sys.exit()

# selective-Repeat():
# Heller enn å slette pakker som er kommet i feil rekkefølge
# skal de buffres og settes på riktig plass.
# Bruke arrays her