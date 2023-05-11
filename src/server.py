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

        # if args.reliablemethod == 'sw':
        #    send_and_wait_server()
        while True:
            # Receiving header from a client
            # data, address = server_socket.recvfrom(1472) # Forslag til å erstatte de tre linjene under
            tuple = server_socket.recvfrom(1472)
            data = tuple[0]
            address = tuple[1]

            header_from_data = data[:12]
            seq, ack, flags, win = parse_header(header_from_data)

            # Used to calculate RTT. Checks if the received data is a ping.
            if b'ping' in data:
                # If ping is found, it will pong back to the sender
                server_socket.sendto(data, address)

                # Continues to the next iteration of the while loop
                continue

            # seq, ack, flags = read_header(data)
            # Hente ut og lese av header

            handshake = handshake_server(flags, server_socket, address)

            if handshake:
                print('Connection established')
            else:
                print('Did not receive ACK from client. Server closing')
                server_socket.close()
                sys.exit()

            if args.reliablemethod == 'saw':
                print('sender nå til saw')
                stop_and_wait(server_socket, args)
            elif args.reliablemethod == 'gbn':
                print('sender nå til gbn')
                go_back_N_server(server_socket, args)
            elif args.reliablemethod == 'sr':
                print('sender nå til sr')
                sel_rep_server(server_socket, args)


def stop_and_wait(server_socket, args):
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

        # Test case skip ack: The server ommits sending ack, so client has to resend
        if args.testcase == 'skip_ack' and seq == 4:
            print('Ack for seq 4 blir nå skippet')
            args.testcase = None
            print(f'args.testcase = {args.testcase}')
            continue

        if flags == 2:
            # Sjekke om pakken som er mottatt inneholder FIN-flagg
            print('Mottatt FIN flagg fra clienten, mottar ikke mer data')
            # Når FIN flagg er mottatt skriver vi dataen til filen.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)

            # Closing the connection gracefully
            close_server(server_socket, address)

        # Hvis seq er større enn null har vi mottatt en datapakke
        elif seq > 0:
            # Lagrer mottatt data i variabelen received_data vha funksjonen receive data
            received_data = receive_data(data, received_data)

            # Oppretter en tilhørende ack-pakke ved å sette ack til å være seq
            ACK_packet = create_packet(0, seq, 0, 64000, b'')

            # Sender ack-pakken til client
            server_socket.sendto(ACK_packet, address)

# Stores packets that arrive in sequence. Sends an ack back to the client for each package that arrived in order
def go_back_N_server(server_socket, args):
    #Variable to store received data in bytes
    received_data = b''
    #Variable to keep track of sequence number of last packet received
    seq_last_packet = 0

    while True:
        # Receiving a message from a client
        data, address = server_socket.recvfrom(1472)

        # Extract header from packet
        header_from_data = data[:12]
        # Read sequence number and flags from header
        seq, ack, flags, win = parse_header(header_from_data)
        print(f'Pakke: {seq} received')

        # Check if flag is 2 (FIN flag enabled)
        if flags == 2:
            print('Received FIN flag from client')
            # finds the size of the amount of data received
            mengde = len(received_data)
            print(f'Received data is: {mengde} bytes')
            # When the FIN flag is received, we write the received bytes to the file.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)

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

def sel_rep_server(server_socket, args):
    # Initialize an empty array called 'buffer' to hold packets that arrive out of order.
    buffer = {}
    # Initialize an empty byte string called 'received_data' to hold the received data.
    received_data = b''
    # Initialize a variable 'seq_last_packet' to hold the sequence number of the last received packet.
    seq_last_packet = 0

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

        # Check if the received packet has the FIN flag set (flags == 2).
        if flags == 2:
            # Print out information that the FIN flag has been received 
            print('Received FIN flag')
            # Print size of received data 
            print(f'Received data: {len(received_data)}')
            # Write received data to file 'received_image.jpg'.
            with open('received_image.jpg', 'wb') as f:
                f.write(received_data)
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
