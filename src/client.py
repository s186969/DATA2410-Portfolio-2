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

    attempts = 0

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
            if seq_client == 1:
                print("Mottok ikke ack for den første!!!")
                print(f'Attempts: {attempts}')
                attempts = attempts + 1
                if attempts >= 5:
                    print("Nå har vi gjort 5 forsøk, og alle blir tapt, så græisfull avslutning")
                    client_socket.close()
                    sys.exit()
            # Pakken må sendes på nytt

    # Closes the connection gracefully
    close_client(client_socket)

#Function that sends n packets at the same time and then wait in m seconds for acknowledgement packet for sent each packet.
# If an acknowledgement number is not received, this function retransmit all packets after 
# last packet that we know was received by server
def go_back_N(client_socket, file_name, testcase, window_size):
    # Initializes the sender window for data in transit
    sender_window = []
    # Initializes a variable that count data sent in bytes
    number_of_data_sent = 0
    # Initializes a variable used to increase the packet number
    seq_client = 1
    # Initializes a variable that keep track of last received ack-packet
    last_ack = 0
    # Initializes an ending variable, used to call the close_client function in the end
    ending = False

    # Reads the picture and converts it to bytes
    with open(file_name, 'rb') as f:
        image_data = f.read()

    # Keep sending packets when the window is not full
    while len(sender_window) < window_size:
   
        # Check if there is space in the sender window to send a new packet
        while number_of_data_sent < len(image_data) and len(sender_window) < window_size:
            # When testcase loss is enabled and sequence number is 3
            if testcase == 'loss' and seq_client == 3:
                print('Seq 3 blir nå skippet')
                # The packet is added to the sender window to simulate that it has been sent
                sender_window.append(seq_client)
                # Disable testcase so that packet 3 can retransmit
                testcase = None
                # Increase sequence number to continue sending
                seq_client += 1
                 # Increase number of bytes sent, since we simulate that  it has been sent
                number_of_data_sent += 1460

                # Break out of the inner loop when the window is full
                if len(sender_window) >= window_size:
                    break

            # Hente ut riktig område av data
            image_data_start = number_of_data_sent
            image_data_stop = image_data_start + 1460
            data = image_data[image_data_start: image_data_stop]


            # Create new packet 
            packet = create_packet(seq_client,0,0,64000,data)
            # Send packet
            client_socket.send(packet)
            print(f'Sent packet number {seq_client}')
            # Increase amount of data sent
            number_of_data_sent += 1460

            # Add package number in sender window 
            sender_window.append(seq_client)
            # Print sender window
            array_as_string = " ".join(str(element) for element in sender_window)
            print(f'Sender window: {array_as_string}')
            # increase packet number
            seq_client += 1


        # Receive acknowledgment from the server as long as there are packets in the sender window
        if len(sender_window) > 0:
            # Wait for acknowledgement during this timeout
            client_socket.settimeout(0.5)
            try:
                # Receive packet
                receive = client_socket.recv(1472)
                # Read acknowledge number from packet header
                seq, ack, flags = read_header(receive)
                print(f'Received ack number: {ack}')
                
                # Check whether the ack number is in the sender_window:
                if ack in sender_window:
                    # Check if the ack number is as expected
                    if ack == last_ack + 1:
                        # Update last_ack variable
                        last_ack = ack  
                        # Remove this ack number from the sender_window
                        sender_window.remove(ack)
                        # Check if sender_window is empty, then sending is over
                        if len(sender_window) == 0:
                            # Setting a variable to be used to exit the outer loop
                            ending = True

                            # Exiting the inner loop
                            break
                        
                        # Print sender window
                        array_as_string = " ".join(str(element) for element in sender_window)
                        print(f'Sender window: {array_as_string}')
                        
                        #Oppdaterer last_ack variabelen
                        #last_ack  = ack
                        continue
            
            #If we do not receive any ack from the server, this indicates packet loss. Packages from this point on must be resent
            except:
                print('Did not receive expected acknowledgement number')
                #Clear sender window
                sender_window.clear()
                
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                #Update number of data sent
                number_of_data_sent = 1460 * last_ack

        # If the sender window is empty, the function has exited the inner loop
        if ending == True:
            # Exiting the outer loop
            break

        #Receive the rest of the acknowledgement numbers after sending is over
        while len(sender_window) > 0 and number_of_data_sent >= len(image_data):
            #Wait this amount of time
            client_socket.settimeout(0.5)
            try:
                #Receive packet from server
                receive = client_socket.recv(1472)
                #Read acknowledgement number from packet header
                seq, ack, flags = read_header(receive)
                print(f'Received acnowledgement number: {ack}')
                
                # Check if the acknowledgement number is in the sender window
                if ack in sender_window:
                    # Remove from sender window if received ack
                    sender_window.remove(ack)
                    #Print updated sender window
                    array_as_string = " ".join(str(element) for element in sender_window)
                    print(f'Sender window: {array_as_string}')
                    continue

            except:
                print('Something went wrong receiving ack')
                #If we do not receive ack from the server, this indicates packet loss. Packages from this point on must be resent
                sender_window.clear()
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                # Update number of data sent
                number_of_data_sent = 1460 * last_ack
                continue

    # Closes the connection gracefully
    close_client(client_socket)


'''
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
    # Bibliotek med pakker som ikke har mottatt ACK, med sekvensnummer som indeks og sendetid som verdi
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
                print('Unacked liste:', str(unacked_packets))
                # Legg til pakken i senderens vindu
                sender_window.append(seq_client)
                # Sett testcase til None for å ikke miste flere pakker
                testcase = None
            else:
                # Send pakken og lagre tidspunktet den ble sendt
                send_time = send_packet(seq_client, image_data)
                # Legg til pakken i ordboken over pakker som ikke har mottatt ACK
                unacked_packets[seq_client] = send_time
                print('Unacked liste:', str(unacked_packets))
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
'''

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
        starttime = time.time()
        # Skriv ut pakkenummer som ble sendt
        print(f'Sendt: {seq_num}')
        return starttime

    def receive_packet():
        # Motta pakke fra serveren
        receive = client_socket.recv(1472)
        # Les headerinformasjonen fra pakken
        seq, ack, flags = read_header(receive)
        # Skriv ut ACK som er mottatt
        print(f'Mottatt: {ack}')

        # Sjekk om ACK er lik det første elementet i senderens vindu
        packet = sender_window[0]
        if ack == packet[0]:
            print(f' Mottatt ack: {ack} og indeks 0 i window: {packet[0]}')
            # Oppdater siste mottatte ACK
            last_ack = ack
            # Fjern pakken fra senderens vindu
            sender_window.remove(packet)
        else:
            print(f' Mottatt ikke forventet ack {ack} og indeks 0 i window: {packet[0]}')
            # Oppdater siste mottatte ACK
            last_ack = ack
            
            for packet in sender_window:
                if ack == packet[0]:
                    # Fjern pakken fra senderens vindu
                    sender_window.remove(packet)
                
            
    def timeout_packet():
        for packet in sender_window:
            seq_num, send_time = packet
            # Sjekk om noen pakker trenger å sendes på nytt på grunn av tidsavbrudd
            current_time = time.time()
            # Hvis det har gått mer enn retransmission_timeout siden pakken ble sendt
            if current_time - send_time > retransmission_timeout:
                # Skriv ut pakkenummer som er resendt på grunn av tidsavbrudd
                print(f' [Timeout] Klargjør resending av pakkenummer: {seq_num}')
                # Send pakken på nytt
                starttime = send_packet(seq_num, image_data)
                sender_window[0] = (seq_num, starttime)
                
    # Funksjon for å simulere pakketap
    def packet_loss(seq_client):
        starttime = time.time()
        # Print ut at pakken ikke blir sendt
        print('Følgende pakke blir ikke sendt: ', seq_client)
        return starttime
        
    # Funksjon for å skrive ut vinduet    
    def print_window():
        # Skriv ut vinduet
        print(f'Window: [{", ".join(str(packet_num) for packet_num, _ in sender_window)}]')
        
    # Initialisere variabler
    sender_window = []  # Liste over pakker i senderens vindu
    # Antall data sendt (i bytes)
    number_of_data_sent = 0
    # Startsekvensnummer for klienten
    seq_client = 1
    # Siste mottatte ACK
    last_ack = 0
    # Retransmisjonstidsavbrudd (i sekunder)
    retransmission_timeout = 0.5

    # Åpne filen i binærmodus og les inn bildedata
    with open(file_name, 'rb') as f:
        # Les inn bildedata
        image_data = f.read()

    # Hovedløkke for å sende pakker og motta ACK-er
    while True:
        # Løkke for å sende pakker til serveren
        while number_of_data_sent < len(image_data) and len(sender_window) < window_size:
            # Hvis vi simulerer tap av pakke 4
            if testcase == 'loss' and seq_client == 4:
                # Kall på funksjon for å simulere pakketap
                starttime = packet_loss(seq_client)
                # Legg til pakken i window-arrayet
                sender_window.append((seq_client, starttime))
                # Sett testcase til None for å ikke simulere pakketap for andre pakker
                testcase = None
                print_window()
            else:
                # Send pakken
                starttime = send_packet(seq_client, image_data)
                # Legg til pakken i senderens vindu
                sender_window.append((seq_client, starttime))
                print_window()
                
            # Oppdater sekvensnummer og antall data sendt
            seq_client += 1
            # Oppdater antall data sendt
            number_of_data_sent += 1460

        try:
            # Kall på funksjon for å motta ACK
            receive_packet()
        except:
            timeout_packet()

        # Avslutt løkken hvis sender_window er tomt
        if not sender_window:
            break
        
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