# Description:
# Imports the necessary libraries
# time: This module provides various time-related functions.
# application: This module contains the application layer functions.
# drtp: This module contains the drtp layer functions.
# header: This module contains the functions for creating and reading the header.
# socket: This module provides low-level networking interface.
# sys: This module provides access to some variables used or maintained by the Python interpreter and to functions that interact strongly with the interpreter.
import time
from application import *
from drtp import *
from header import *
from socket import *
import sys

# Description:
# Function that establishes a reliable connection with the server
# Arguments: 
# args: The arguments from the command line
# Returns: None
def start_client(args):
    # Defining the IP address using the '-i' flag
    ip_address = args.serverip
    # Defining the port number using the '-p' flag
    port_number = args.port
    # Defining the file name using the '-f' flag
    file_name = args.filename
    # Create a UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)
    # Bind the socket to the port
    client_socket.connect((ip_address, port_number))

    # Establish reliable connection with handshake
    handshake_client(client_socket)

    # Send data using stop and wait
    if args.reliablemethod == 'saw':
        stop_and_wait(client_socket, file_name, args)

    # Send data using Go back N
    elif args.reliablemethod == 'gbn':
        go_back_N(client_socket, file_name, args)

    # Send data using Selective Repeat
    elif args.reliablemethod == 'sr':
        sel_rep(client_socket, file_name, args.testcase, args.windowsize, args.bonus)
    
    # If no reliable method is chosen, the program will print an error message and exit
    else:
        print('No reliable method chosen')

# Description:
# Function that sends data using stop and wait
# Arguments: 
# client_socket: The socket used to send data
# file_name: The name of the file to be sent
# args: The arguments from the command line
# Returns: None
def stop_and_wait(client_socket, file_name, args):
    # Defining the sequence number
    seq_client = 1
    # Defining the acknowledgement number
    ack_client = 0
    # Keep track of the amount of data sent
    number_of_data_sent = 0
    # Counter for failed attempts
    attempts = 0

    # Read the image file and store its data in 'image_data'
    with open(file_name, 'rb') as f:
        image_data = f.read()

    # Initial round-trip time value
    round_trip_time = 0.5

    # Continue sending data until the entire image has been sent
    while number_of_data_sent < len(image_data):
        # Extract the correct 1460 bytes of image data to send
        image_data_start = number_of_data_sent
        image_data_stop = image_data_start + 1460
        data = image_data[image_data_start: image_data_stop]

        # Create a packet with header and data using the create_packet function
        packet = create_packet(seq_client, ack_client, 0, 64000, data)

        # Handle packet loss based on the 'testcase' argument
        if args.testcase == 'loss' and seq_client == 4:
            # Print a message to the user
            print('Seq 4 blir nå skippet')
            # Set the 'testcase' argument to None so that the next packet will not be skipped
            testcase = None
            # Print the testcase to the user
            print(f'args.testcase = {testcase}')
            continue

        # Start time duration RTT
        start_round_trip_time = time.time()

        # Send the packet and display sequence number
        print(f'Sender pakke med seq: {seq_client}')
        client_socket.send(packet)

        # Set the client socket timeout to the current round-trip time
        client_socket.settimeout(round_trip_time)
        print(f'Timeout is set to {round_trip_time} s')

        # Variable to check for duplicate ACKs
        dupack = 0
        try:
            # Receive ACK from the server
            receive = client_socket.recv(1472)
            # Read the header of the received packet
            seq, ack, flags = read_header(receive)
            # Print the received ACK to the user
            print(f'Mottatt pakke med ack: {ack}')

            # Update RTT if 'bonus' argument is set
            if args.bonus:
                round_trip_time = 4 * (time.time() - start_round_trip_time)

            # Check if received ACK matches the sequence number
            if ack == seq_client:
                dupack += 1
                # Check if duplicate ACKs have been received
                if dupack > 1:
                     # Packet needs to be resent
                    continue
                else:
                    # Update the sequence number
                    number_of_data_sent += len(data)
                    seq_client += 1
            else:
                continue
        except:
            # Handle the case when the first ACK is not received
            if seq_client == 1:
                print(" Did not recieve ack for the first packet!")
                print(f'Attempts: {attempts}')
                attempts = attempts + 1
                if attempts >= 5:
                    print("Did not recieve ack for 5 attempts, so we close the connection")
                    client_socket.close()
                    # Exit the program
                    sys.exit()
                    
    # Closes the connection gracefully
    close_client(client_socket)

# Description:
# Creates and sends a data packet using the given image data, sequence number, and client socket.
# Arguments: 
# image_data (bytes): The image data to be sent.
# seq_client (int): The current sequence number for the packet.
# client_socket (socket): The client socket to send the packet over.
# Returns: 
# data (bytes): The portion of image data that was sent in the packet.
def create_and_send_datapacket(image_data, seq_client, client_socket):
    # Calculate the total number of data bytes sent so far
    number_of_data_sent = ((seq_client - 1) * 1460)
    # Extract the correct 1460 bytes of image data to send
    image_data_start = number_of_data_sent
    image_data_stop = image_data_start + 1460
    data = image_data[image_data_start: image_data_stop]

    # Create a new packet with header and data using the create_packet function
    packet = create_packet(seq_client,0,0,64000,data)
    # Send the packet using the client socket
    client_socket.send(packet)
    # Print the sequence number of the packet that was sent
    print(f'Sent packet number {seq_client}')
    # Return the data that was sent
    return data

# Description:
# Implements the Go-Back-N protocol to send a file over a client socket.
# Arguments: 
# client_socket (socket): The client socket to send the file over.
# file_name (str): The file to be sent.
# args (Namespace): The arguments containing optional settings for the protocol, such as window size, test case, and bonus.
# Returns: None
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

    # Initial round-trip time value
    round_trip_time = 0.5

    start_round_trip_time = {}

    # Keep sending packets when the window is not full or when retransmission is needed
    while len(sender_window) < args.windowsize or retransmission == True:
        # Check if there is space in the sender window to send a new packet and if there is data left to send
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

            # Create and send a data packet
            data = create_and_send_datapacket(image_data, seq_client, client_socket)

            # Start time duration RTT
            start_round_trip_time[seq_client] = time.time()

            # Increase amount of data sent
            number_of_data_sent += 1460

            # Add package number in sender window 
            sender_window.append(seq_client)
            # Print sender window
            array_as_string = " ".join(str(element) for element in sender_window)
            
            # If the sender window is full, print it
            if len(sender_window) == args.windowsize:
                print(f'Sender window: {array_as_string}')
            # Increase packet number
            seq_client += 1

        # Receive acknowledgment from the server as long as there are packets in the sender window
        if len(sender_window) > 0:
            # Wait for acknowledgement during this timeout
            client_socket.settimeout(round_trip_time)
            print(f'Timeout is set to {round_trip_time} s')

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

                        # Update RTT if 'bonus' argument is set
                        if args.bonus:
                            round_trip_time = 4 * (time.time() - start_round_trip_time[ack])
                            print(f'RTT for packet {ack}: {time.time() - start_round_trip_time[ack]} s')

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
                        # If ack number is not = last ack + 1, then the ack number is not as expected 
                        continue
                    
            # If we do not receive any ack from the server, this indicates packet loss. Packages from this point on must be resent
            except:
                # Print that we did not receive the expected ack number
                print('\nDid not receive expected acknowledgement number')                
                # Increment the sequence number to the next packet to be sent 
                seq_client = last_ack + 1
                # Print that we are retransmitting
                print('Retransmit packets in sender window')
                # Retransmit all packets in the sender window
                for packet in sender_window:
                    # Create and send datapacket
                    data = create_and_send_datapacket(image_data, seq_client, client_socket)

                    # Start time duration RTT
                    start_round_trip_time[seq_client] = time.time()

                    # Print sender Window
                    array_as_string = " ".join(str(element) for element in sender_window)
                    # Print sender window
                    print(f'Sender window: {array_as_string}')
                    # Increase seq_client
                    seq_client += 1
                  
                # Sends the package after the previous one that we know has arrived
                number_of_data_sent = number_of_data_sent
                # The variable makes it possible to continue with the outer while loop even if the sending window is full
                retransmission = True
                
        # If the sender window is empty, the function has exited the inner loop
        if ending == True:
            # Exiting the outer loop
            break

        # Receive the rest of the acknowledgement numbers after sending is over
        while len(sender_window) > 0 and number_of_data_sent >= len(image_data):
            #Wait this amount of time
            client_socket.settimeout(round_trip_time)
            print(f'Timeout is set to {round_trip_time} s')

            try:
                # Receive packet from server
                receive = client_socket.recv(1472)
                # Read acknowledgement number from packet header
                seq, ack, flags = read_header(receive)
                print(f'Received acnowledgement number: {ack}')
                
                # Check if the acknowledgement number is in the sender window
                if ack in sender_window:
                    # Remove from sender window if received ack
                    sender_window.remove(ack)

                    # Update RTT if 'bonus' argument is set
                    if args.bonus:
                        print(f'RTT for packet {ack}: {time.time() - start_round_trip_time[ack]} s')
                        round_trip_time = 4 * (time.time() - start_round_trip_time[ack])

                    if len(sender_window) == 0:
                        ending = True

                    #Print updated sender window
                    array_as_string = " ".join(str(element) for element in sender_window)
                    print(f'Sender window: {array_as_string}')
                        
                    continue

            except:
                # Print that we did not receive the expected ack number
                print('Something went wrong receiving ack')
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                # Update number of data sent
                number_of_data_sent = 1460 * last_ack
                continue

    # Closes the connection gracefully
    close_client(client_socket)

# Description: 
# This function implements the selective repeat protocol. It sends the file to the server, and handles the retransmission of lost packets. 
# Arguments: 
# client_socket: The socket used to communicate with the server
# file_name: The name of the file to be sent 
# testcase: The testcase to be used
# window_size: The size of the window to be used
# Returns: None
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

    # Initial round-trip time value
    round_trip_time = 0.5

    start_round_trip_time = {}

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

            # Start time duration RTT
            start_round_trip_time[seq_client] = time.time()

            # Add package number in sender window 
            if not retransmission:
                sender_window.append(seq_client)

            # Print sender window
            array_as_string = " ".join(str(element) for element in sender_window)
            if len(sender_window) == window_size:
                print(f'Sender window: {array_as_string}')

            # Increase packet number
            seq_client += 1
            # Used when no ack was received (exception), and all packets in sender window is retransmitted. 
            # The variable must be kept True for each packet in the window
            if retransmission and i < len(sender_window):
                retransmission = True
                i += 1
            else:
                retransmission = False
            
            # Update waiting variable
            waiting = False

        # Clear i-variable for next use of while-loop
        i = 0

        # Receive acknowledgment from the server as long as there are packets in the sender window
        if len(sender_window) > 0 and number_of_data_sent < len(image_data):
            # Wait for acknowledgement during this timeout
            client_socket.settimeout(round_trip_time)
            print(f'Timeout is set to {round_trip_time} s')

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
                    if bonus:
                        print(f'RTT for packet {ack}: {time.time() - start_round_trip_time[ack]} s')
                        round_trip_time = 4 * (time.time() - start_round_trip_time[ack])


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
                        # Print that we are waiting for ack
                        print('Waiting for ack')
                        continue    
                
            #If we do not receive any ack from the server, this indicates packet loss. Packages from this point on must be resent
            except:
                # Print that we did not receive expected ack
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

        # If the sender window is empty, the function has exited the inner loop
        if ending == True:
            # Exiting the outer loop
            print('Ending true')
            break
    
        # Receive the rest of the acknowledgement numbers after sending is over
        while len(sender_window) > 0 and number_of_data_sent >= len(image_data):
            # Wait this amount of time
            client_socket.settimeout(0.5)

            try:
                # Receive packet from server
                receive = client_socket.recv(1472)
                # Read acknowledgement number from packet header
                seq, ack, flags = read_header(receive)
                print(f'Received acnowledgement number: {ack}')
                
                # When ack number is equal to last seq number in sender window and the ack_array is empty, sending is over.
                if ack == sender_window[-1] and len(ack_array) == 0: 
                    ending = True 
                
                # If we receive the ack for the first packet in the sender window, and there is packets in ack array, we know that all packets in the sender window is reveived by the server
                if ack == sender_window[0] and len(ack_array) > 0:
                    # Clear sender window
                    sender_window.clear()
                    # Clear ack_array
                    ack_array.clear()
                    # Update ending variable
                    ending = True

                # Check if the acknowledgement number is in the sender window and check if the ack number is as expected    
                elif ack in sender_window and ack == last_ack +1:
                    # Update last_ack variable
                    last_ack = ack  
                    # Remove this ack number from the sender_window
                    sender_window.remove(ack)
                    continue
                else:
                    # Ack in window, but in the wrong order. Saving in ack_array. 
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

            except:
                print('Something went wrong receiving ack')
                #If we do not receive ack from the server, this indicates packet loss. Packages from this point on must be resent
                #Sends the package after the previous one that we know has arrived
                seq_client = last_ack + 1
                data = create_and_send_datapacket(image_data, seq_client, client_socket)
                # Retransmission is set to True and used in while-loop to send all packets in window again
                retransmission = True
                continue

    # Closes the connection gracefully
    print('Close_Client called')
    close_client(client_socket)