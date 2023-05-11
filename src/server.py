# Description:
# Imports the necessary libraries
# socket: This module provides low-level networking interface.
# application: This module contains the application layer functions.
# drtp: This module contains the drtp layer functions.
# header: This module contains the functions for creating and reading the header.
# time: This module provides various time-related functions.
from socket import *
from application import *
from drtp import *
from header import *
import time

# Description:
# This function appends the received data payload to received_data buffer.
# Arguments: 
# data (bytes): The received data, including the header.
# received_data (bytes): The buffer storing previously received data.
# Returns: 
# received_data: The updated received_data buffer containing the newly received data payload.
def receive_data(data, received_data):
    received_data += data[12:]
    return received_data

# Description:
# This function starts the server, listens for incoming connections, and handles the connection with the appropriate reliable data transfer method based on the command line arguments.
# Arguments: 
# args: Parsed command line arguments containing the server IP, port, and reliable data transfer method.
# Returns: None
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

        while True:
            # Receiving header from a client
            data, address = server_socket.recvfrom(1472)

            # Extracting the header from the received data
            header_from_data = data[:12]
            seq, ack, flags, win = parse_header(header_from_data)

            # Used to calculate RTT. Checks if the received data is a ping.
            if b'ping' in data:
                # If ping is found, it will pong back to the sender
                server_socket.sendto(data, address)

                # Continues to the next iteration of the while loop
                continue          
            
            # Perform handshake with the client and establish a connection
            handshake = handshake_server(flags, server_socket, address)

            # If the handshake is successful, the server will continue to the next step
            if handshake:
                print('Connection established')
            else:
                print('Did not receive ACK from client. Server closing')
                server_socket.close()
                sys.exit()

            # If the reliable data transfer method is 'stop-and-wait', the server will use the stop_and_wait function
            if args.reliablemethod == 'saw':
                print('Sending to Stop-and-Wait')
                stop_and_wait(server_socket, args)
            # If the reliable data transfer method is 'go-back-N', the server will use the go_back_N_server function
            elif args.reliablemethod == 'gbn':
                print('Sending to Go-Back-N')
                go_back_N_server(server_socket, args)
            # If the reliable data transfer method is 'selective-repeat', the server will use the sel_rep_server function
            elif args.reliablemethod == 'sr':
                print('Sending to Selective Repeat')
                sel_rep_server(server_socket, args)

# Description:
# This function implements the Stop-and-Wait reliable data transfer method for the server. It receives data from the client and sends an acknowledgement for each received packet.
# Arguments: 
# server_socket: The socket object for the server to receive and send data.
# args: Parsed command line arguments containing the test case.
# Returns: None
def stop_and_wait(server_socket, args):
    received_data = b''

    # Starting value of the received bytes for calculating throughput
    total_bytes_received = 0

    while True:
        # Receiving a message from a client
        data, address = server_socket.recvfrom(1472)

        # Extract header from packet
        header_from_data = data[:12]
        seq, ack, flags, win = parse_header(header_from_data)

        # Accumulated values of bytes for calculating throughput 
        total_bytes_received = total_bytes_received + len(data)

        if seq == 1:
            # Starting time in seconds for calculating throughput
            starting_time = time.time()

        # Test case skip ack: The server ommits sending ack, so client has to resend
        if args.testcase == 'skip_ack' and seq == 4:
            print('Ack for seq 4 is being skipped')
            args.testcase = None
            print(f'args.testcase = {args.testcase}')
            continue

        if flags == 2:
            # Check if the packet received contains a FIN flag
            print('Received FIN flag from the client, not receiving more data')
            # Write to the file when FIN flag is received
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)
            
            # Ending time for calculating throughput
            ending_time = time.time()

            # Duration of the transfer for calculating throughput
            duration_time = ending_time - starting_time

            # Calculation of the throughput
            throughput = (total_bytes_received * 8e-6) / duration_time

            print(f'Total bytes received: {total_bytes_received} bytes')
            print(f'Duration: {duration_time:.2f} s')
            print(f'Throughput: {throughput:.2f} Mbps')

            # Closing the connection gracefully
            close_server(server_socket, address)

        # If seq is greater than zero, we have received a data packet.
        elif seq > 0:
            # Storing received data in the variable received_data using the function receive_data.
            received_data = receive_data(data, received_data)

            # Creating a corresponding ack-packet by setting ack to be seq.
            ACK_packet = create_packet(0, seq, 0, 64000, b'')

            # Sending the ack-packet to the client.
            server_socket.sendto(ACK_packet, address)

# Description:
# This function implements the Go-Back-N reliable data transfer method for the server. It receives data from the client and sends acknowledgements for the packets received in order.
# Arguments: 
# server_socket: The socket object for the server to receive and send data.
# args: Parsed command line arguments containing the test case.
# Returns: None
def go_back_N_server(server_socket, args):
    #Variable to store received data in bytes
    received_data = b''
    #Variable to keep track of sequence number of last packet received
    seq_last_packet = 0

    # Starting value of the received bytes for calculating throughput
    total_bytes_received = 0

    while True:
        # Receiving a message from a client
        data, address = server_socket.recvfrom(1472)
        # Extract header from packet
        header_from_data = data[:12]
        # Read sequence number and flags from header
        seq, ack, flags, win = parse_header(header_from_data)
        print(f'Packet: {seq} received')

        # Accumulated values of bytes for calculating throughput 
        total_bytes_received = total_bytes_received + len(data)

        if seq == 1:
            # Starting time in seconds for calculating throughput
            starting_time = time.time()

        # Check if flag is 2 (FIN flag enabled)
        if flags == 2:
            print('Received FIN flag from client')
            # finds the size of the amount of data received
            mengde = len(received_data)
            print(f'Received data is: {mengde} bytes')
            # When the FIN flag is received, we write the received bytes to the file.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)

            # Ending time for calculating throughput
            ending_time = time.time()

            # Duration of the transfer for calculating throughput
            duration_time = ending_time - starting_time

            # Calculation of the throughput
            throughput = (total_bytes_received * 8e-6) / duration_time

            print(f'Total bytes received: {total_bytes_received} bytes')
            print(f'Duration: {duration_time:.2f} s')
            print(f'Throughput: {throughput:.2f} Mbps')

            # Closing the connection gracefully
            close_server(server_socket, address)

        # check if the package we have received is the next in order
        if seq == seq_last_packet + 1:
            # Check if testcase skip_ack is enabled
            if args.testcase == 'skip_ack' and seq == 4:
                print('Does not send ACK')
                # Disable test case so that the packet can retransmit
                args.testcase = None
                continue
            else:
                # Creates an associated ack packet by setting ack to be seq
                ACK_packet = create_packet(0, seq, 0, 64000, b'')

                # Sending ack-packet to client
                server_socket.sendto(ACK_packet, address)
                # Put the package's data into the received_data variable
                received_data = receive_data(data, received_data)
                # Update sequence number of last reveived packet
                seq_last_packet = seq
        else:
            print(f'Packet {seq} received in the wrong order')
            continue

# Description:
# This function implements the Selective Repeat reliable data transfer method for the server.It receives data from the client and sends acknowledgements for the packets received. It also handles out-of-order packets by buffering them and processing them in the correct order.
# Arguments: 
# server_socket: The socket object for the server to receive and send data.
# args: Parsed command line arguments containing the test case.
# Returns: None
def sel_rep_server(server_socket, args):
    # Initialize an empty array called 'buffer' to hold packets that arrive out of order.
    buffer = {}
    # Initialize an empty byte string called 'received_data' to hold the received data.
    received_data = b''
    # Initialize a variable 'seq_last_packet' to hold the sequence number of the last received packet.
    seq_last_packet = 0

    # Starting value of the received bytes for calculating throughput
    total_bytes_received = 0

    # Start an infinite loop to receive packets from the client.
    while True:
        # Receive data and address from client through server_socket
        data, address = server_socket.recvfrom(1472)
        # Get header information from packet
        header_from_data = data[:12]
        # Parse the header information to retrieve the sequence number, ACK number, flags, and window size
        seq, ack, flags, win = parse_header(header_from_data)
        # Print information about the packet
        print(f'Packet: {seq} received')

        # Accumulated values of bytes for calculating throughput 
        total_bytes_received = total_bytes_received + len(data)

        if seq == 1:
            # Starting time in seconds for calculating throughput
            starting_time = time.time()

        # Check if the received packet has the FIN flag set (flags == 2).
        if flags == 2:
            # Print out information that the FIN flag has been received 
            print('Received FIN flag')
            # Print size of received data 
            print(f'Received data: {len(received_data)}')
            # Write received data to file 'received_image.jpg'.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)


            # Ending time for calculating throughput
            ending_time = time.time()

            # Duration of the transfer for calculating throughput
            duration_time = ending_time - starting_time

            # Calculation of the throughput
            throughput = (total_bytes_received * 8e-6) / duration_time

            print(f'Total bytes received: {total_bytes_received} bytes')
            print(f'Duration: {duration_time:.2f} s')
            print(f'Throughput: {throughput:.2f} Mbps')

            #Close server
            close_server(server_socket, address)
            
        # Check if the sequence number of the received packet is one more than the sequence number of the last received packet.
        if seq == seq_last_packet + 1:
            # Handle a test case where the server should skip sending an ACK for the packet with sequence number 4.
            if args.testcase == 'skip_ack' and seq == 4:
                print('Does not send ack')
                # Disable testcase so that packet 4 can be saved 
                args.testcase = None
            else:
                # Create ack-packet for the packet received
                ACK_packet = create_packet(0, seq, 0, 64000, b'')
                # Send ack-packet to client
                server_socket.sendto(ACK_packet, address)
                print(f'Sending ack: {seq}')
                # Saving received data in the variable 'received_data'.
                received_data = receive_data(data, received_data)
                # Update seq number of last received packet
                seq_last_packet = seq
                # Print buffer when not empty
                if len(buffer) > 0:
                    array_as_string = " ".join(str(element) for element in buffer)
                    print(f'\nBuffer: {array_as_string}\n')
                # If there are packets in the buffer with sequence numbers greater than the last received packet, handle and remove them from the buffer.
                while seq_last_packet + 1 in buffer:
                    # Update seq number of last received packet
                    seq_last_packet += 1
                    # Update amount of received data
                    received_data = receive_data(buffer[seq_last_packet], received_data)
                    # Delete element from buffer
                    del buffer[seq_last_packet]
                    
        # Packet not received in order, saved to buffer and sending ack
        elif seq != 0:
            print('Packet not in order, save in buffer and sending ack')
            #Adding data to buffer
            buffer[seq] = data
            # Create ack packet
            ACK_packet = create_packet(0, seq, 0, 64000, b'')
            # Send ack packet
            server_socket.sendto(ACK_packet, address)
