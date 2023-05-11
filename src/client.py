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

    # Establish reliable connection with handshake
    handshake_client(client_socket)

    # Sende data ved å bruke stop and wait
    if args.reliablemethod == 'saw':
        stop_and_wait(client_socket, file_name, args)

    # Sende data ved å bruke Go back N
    elif args.reliablemethod == 'gbn':
        go_back_N(client_socket, file_name, args)

    # Sende data ved å bruke Selective Repeat
    elif args.reliablemethod == 'sr':
        sel_rep(client_socket, file_name, args.testcase, args.windowsize, args.bonus)

    # Denne kan vi nok ta bort når vi er ferdige
    else:
        send_data(client_socket, file_name)


def stop_and_wait(client_socket, file_name, args):
    seq_client = 1
    ack_client = 0

    # Holde kontroll på data sendt
    number_of_data_sent = 0

    attempts = 0

    # Leser bildet oslomet.jpg og sender dette til server
    with open(file_name, 'rb') as f:
        image_data = f.read()

    round_trip_time = 0.5

    # Så lenge vi ikke har sendt hele bildet, fortsetter vi å sende
    while number_of_data_sent < len(image_data):
        # Må hente ut riktige 1460 bytes av arrayet med image-data
        image_data_start = number_of_data_sent
        image_data_stop = image_data_start + 1460
        data = image_data[image_data_start: image_data_stop]

        # Bruker metode fra header.py til å lage pakke med header og data
        packet = create_packet(seq_client, ack_client, 0, 64000, data)

        if args.testcase == 'loss' and seq_client == 4:
            print('Seq 4 blir nå skippet')
            testcase = None
            print(f'args.testcase = {testcase}')
            continue

        # Start time duration RTT
        start_round_trip_time = time.time()

        print(f'Sender pakke med seq: {seq_client}')
        client_socket.send(packet)

        # Venter på ack fra server
        client_socket.settimeout(round_trip_time)
        print(f'Timeout is set to {round_trip_time} s')

        # Variabel for å sjekke om man har mottatt to akc på samme pakke
        dupack = 0
        try:
            receive = client_socket.recv(1472)
            seq, ack, flags = read_header(receive)
            print(f'Mottatt pakke med ack: {ack}')

            # End time duration RTT
            end_round_trip_time = time.time()

            # New RTT
            if args.bonus:
                round_trip_time = 4 * (end_round_trip_time - start_round_trip_time)

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


def create_and_send_datapacket(image_data, seq_client, client_socket):
    number_of_data_sent = ((seq_client - 1) * 1460)
    # Hente ut riktig område av data
    image_data_start = number_of_data_sent
    image_data_stop = image_data_start + 1460
    data = image_data[image_data_start: image_data_stop]

    # Create new packet 
    packet = create_packet(seq_client,0,0,64000,data)
    # Send packet
    client_socket.send(packet)
    print(f'Sent packet number {seq_client}')

    return data

#Function that sends n packets at the same time and then wait in m seconds for acknowledgement packet for sent each packet.
# If an acknowledgement number is not received, this function retransmit all packets after 
# last packet that we know was received by server
def go_back_N(client_socket, file_name, args):
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
    while len(sender_window) < args.windowsize or retransmission == True:
   
        # Check if there is space in the sender window to send a new packet
        while number_of_data_sent < len(image_data) and len(sender_window) < args.windowsize:
            # When testcase loss is enabled and sequence number is 3
            if args.testcase == 'loss' and seq_client == 3:
                print('\nSeq 3 is now skipped\n')
                # The packet is added to the sender window to simulate that it has been sent
                sender_window.append(seq_client)
                # Disable testcase so that packet 3 can retransmit
                args.testcase = None
                # Increase sequence number to continue sending
                seq_client += 1
                 # Increase number of bytes sent, since we simulate that  it has been sent
                number_of_data_sent += 1460

                # Break out of the inner loop when the window is full
                if len(sender_window) >= args.windowsize:
                    break

            # Hente ut riktig område av data
            data = create_and_send_datapacket(image_data, seq_client, client_socket)

            # Increase amount of data sent
            number_of_data_sent += 1460

            # Add package number in sender window 
            sender_window.append(seq_client)
            # Print sender window
            array_as_string = " ".join(str(element) for element in sender_window)
            if len(sender_window) == args.windowsize:
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
                print(f'\nReceived ack number: {ack}')

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
                        
                        #Oppdaterer last_ack variabelen
                        #last_ack  = ack
                        continue
            
        
            #If we do not receive any ack from the server, this indicates packet loss. Packages from this point on must be resent
            except:
                print('\nDid not receive expected acknowledgement number')
                #Clear sender window
                #sender_window.clear()
                seq_client = last_ack + 1
                print('Retransmit packets in sender window')

                for packet in sender_window:
                    # Create and send datapacket
                    data = create_and_send_datapacket(image_data, seq_client, client_socket)

                    # Print sender Window
                    array_as_string = " ".join(str(element) for element in sender_window)
                    print(f'Sender window: {array_as_string}')
                    # Increase seq_client
                    seq_client += 1
                  
                #Sends the package after the previous one that we know has arrived
                number_of_data_sent = number_of_data_sent
                # The variable makes it possible to continue with the outer while loop even if the sending window is full
                retransmission = True
                
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

                    if len(sender_window) == 0:
                        ending = True

                    #Print updated sender window
                    array_as_string = " ".join(str(element) for element in sender_window)
                    print(f'Sender window: {array_as_string}')
                        
                    continue

            except:
                print('Something went wrong receiving ack')
                #If we do not receive ack from the server, this indicates packet loss. Packages from this point on must be resent
                #sender_window.clear()
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                # Update number of data sent
                number_of_data_sent = 1460 * last_ack
                continue

    # Closes the connection gracefully
    close_client(client_socket)

def sel_rep(client_socket, file_name, testcase, window_size, bonus):
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
    # Initializes an waiting variable, used to continue looping while waiting for ack
    waiting = False
    # Initializes an retransmission variable, used to continue looping after retransmission, waiting for ack
    retransmission = False
    # Initializes an array to save the ack received in wrong order
    ack_array = []
  
    # Reads the picture and converts it to bytes
    with open(file_name, 'rb') as f:
        image_data = f.read()

    # Enter while-loop to keep sending packets when the window is not full, or to wait for ack, or to wait for ack after retransmit 
    while len(sender_window) < window_size or waiting == True or retransmission == True:
        if ending == True:
        # Exiting the outer loop
            print('Ending')
            break
        if number_of_data_sent >= len(image_data):
            break

        # Check if there is space in the sender window to send a new packet
        i = 0
        while (number_of_data_sent < len(image_data) and len(sender_window) < window_size) or retransmission:
            # When testcase loss is enabled and sequence number is 3
            if testcase == 'loss' and seq_client == 3:
                print('\nSeq 3 blir nå skippet\n')
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
            
            # Increase amount of data sent for eack new packet
            if not retransmission:
                number_of_data_sent += 1460

            # Create and send a datapacket using this function
            data = create_and_send_datapacket(image_data, seq_client, client_socket)

            # Add package number in sender window 
            if not retransmission:
                sender_window.append(seq_client)

            # Print sender window
            array_as_string = " ".join(str(element) for element in sender_window)
            if len(sender_window) == window_size:
                print(f'Sender window: {array_as_string}')

            # increase packet number
            seq_client += 1
            # Used when no ack was received (exception), and all packets in sender window is retransmitted. 
            # The variable must be kept True for each packet in the window
            if retransmission and i < len(sender_window):
                retransmission = True
                i += 1
            else:
                retransmission = False
            
            # Kan vi ta denne bort?
            waiting = False

        # Clear i-variable for next use of while-loop
        i = 0

        # Receive acknowledgment from the server as long as there are packets in the sender window
        if len(sender_window) > 0 and number_of_data_sent < len(image_data):
            # Wait for acknowledgement during this timeout
            client_socket.settimeout(0.5)

            try:
                # Receive packet
                receive = client_socket.recv(1472)
                # Read acknowledge number from packet header
                seq, ack, flags = read_header(receive)
                print(f'\nReceived ack number: {ack}')
                
                # If ack is equal to first seq in window and the ack_array contains ack for the rest of the packets in window,
                # we know that all packets in window is received  
                if ack == sender_window[0] and len(ack_array) > 0:
                    # Clear sender window
                    sender_window.clear()

                    # Clear ack_array
                    ack_array.clear()

                    # We know that all seq in window was now acked. 
                    last_ack += window_size
                    
                # Check whether the ack number is in the sender_window:
                if ack in sender_window:
                    # Check if the ack number is as expected
                    if ack == last_ack + 1:
                        # Update last_ack variable
                        last_ack = ack  
                        # Remove this ack number from the sender_window
                        sender_window.remove(ack)
                        continue
                    # Ack was not in order, added to ack_array. 
                    else:
                        ack_array.append(ack)
                        # Window is full, we have to wait for more ack
                        waiting = True
                        print('Waiting for ack')
                        continue    
                
            #If we do not receive any ack from the server, this indicates packet loss. Packages from this point on must be resent
            except:
                print('\nDid not receive expected acknowledgement number')
                array_as_string = " ".join(str(element) for element in ack_array)
                print(f'Ack_array: {array_as_string}\n')
                
                # The packet after last ack is lost, resend
                seq_client = last_ack + 1

                # Retransmit lost packet
                data = create_and_send_datapacket(image_data, seq_client, client_socket)

                # Print sender window
                array_as_string = " ".join(str(element) for element in sender_window)
                print(f'Sender window: {array_as_string}')
                
                # Print array with acknowledgement numbers not received in order
                array_as_string = " ".join(str(element) for element in ack_array)
                print(f'Ack_array: {array_as_string}')
               
                # The rest of the window is alredy acked, can now continue
                seq_client += window_size

        # Kan vi ta bort denne?
        # If the sender window is empty, the function has exited the inner loop
        if ending == True:
            # Exiting the outer loop
            print('Ending true')
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
                
                # When ack number is equal to last seq number in sender window and the ack_array is empty, sending is over.
                if ack == sender_window[-1] and len(ack_array) == 0: 
                    ending = True 
                
                #If we receive the ack for the first packet in the sender window, and there is packets in ack array,
                # we know that all packets in the sender window is reveived by the server
                if ack == sender_window[0] and len(ack_array) > 0:
                    sender_window.clear()
                    ack_array.clear()
                    ending = True
                    #last_ack += window_size
                    #retransmission = False

                # Check if the acknowledgement number is in the sender window and check if the ack number is as expected    
                elif ack in sender_window and ack == last_ack +1:
                    # Update last_ack variable
                    last_ack = ack  
                    # Remove this ack number from the sender_window
                    sender_window.remove(ack)
                    continue
                else:
                    #Ack in window, but in the wrong order. Saving in ack_array. 
                    ack_array.append(ack)
                    print('Received ack in wrong order, saved')
                    # The packet after last ack is lost, resend
                    if len(ack_array) == 0:
                        seq_client = last_ack + 1
                        data = create_and_send_datapacket(image_data, seq_client, client_socket)  
                    # Waiting variable set to True, to keep looping while waiting for the right ack-packet
                    print(f'Number of data sent: {number_of_data_sent}')
                    array_as_string = " ".join(str(element) for element in ack_array)
                    print(f'Ack_array: {array_as_string}\n')
                    print(f'Bildedata: {len(image_data)}')
                    waiting = True
                    # Continue looping
                    #continue    

            except:
                print('Something went wrong receiving ack')
                #If we do not receive ack from the server, this indicates packet loss. Packages from this point on must be resent
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                data = create_and_send_datapacket(image_data, seq_client, client_socket)
                # Update number of data sent
                #number_of_data_sent = 1460 * last_ack
                # Retransmission is set to True and used in while-loop to send all packets in window again
                retransmission = True
                continue

    # Closes the connection gracefully
    print('Close_Client kalles')
    close_client(client_socket)
