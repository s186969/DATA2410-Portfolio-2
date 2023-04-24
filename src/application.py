from socket import *
import argparse
import sys
import threading
import ipaddress

# This function will parse the command-line arguments and perform basic error checking
def parse_args():
    # Defines and parses the command-line argument
    parser = argparse.ArgumentParser(description = 'Reliable Data Transfer Protocol Application')
    # '-s' flag: Enables the server mode
    parser.add_argument('-s', '--server', action = 'store_true', help = "Enables server mode")

    # '-c' flag: Enables the client mode
    parser.add_argument('-c', '--client', action = 'store_true', help = "Enables client mode")

    # '-b' flag: Sets the IP address of the server to bind to. Default value is '127.0.0.1'
    parser.add_argument('-b', '--bind', type = str, default = '127.0.0.1', help = "Selects the IP address of the server's interface")

    # '-I' flag: Sets the IP address of the server that the client will connect to. Default value is '127.0.0.1'
    parser.add_argument('-I', '--serverip', type= str, default = '127.0.0.1', help = "Selects the IP address of server")

    # '-p' flag: Sets the port number that the server will listen on or the client will connect to. The default value is 8088
    parser.add_argument('-p', '--port', type = int, default = 8088, help = "Selects the port number")

    # Parsing the command-line arguments
    args = parser.parse_args()

    # Checks conditions for flags
    validate_args(args)

    # Returns the parsed command-line arguments
    return args

    # This function will validate the arguments from above
def validate_args(args):
    # Checks if both '-s' flag and '-c' flag are enabled at the same time
    if args.server and args.client:
        sys.exit("Error: You cannot run both server and client mode at the same time")

    # Checks if neither '-s' flag nor '-c' flag is enabled
    if not (args.server or args.client):
        sys.exit("Error: You must run either in server or client mode")

    # Checks if '-b' flag have a valid IP address
    try:
        ipaddress.ip_address(args.bind)
    except ValueError:
        sys.exit("Error: Invalid IP address for '-b' flag")

    # Checks if '-I' flag have a valid IP address
    try:
        ipaddress.ip_address(args.serverip)
    except ValueError:
        sys.exit("Error: Invalid IP address for '-I' flag")
    
    # Checks if the port number for the '-p' flag is between 1024 and 65535
    if args.port < 1024 or args.port > 65535:
        sys.exit("Error: Invalid value for '-p' flag. The port must be an integer in the range [1024, 65535]")
    

def start_server(args):
    # Defining the IP address using the '-b' flag
    ip_address = args.bind
    
    # Defining the port number using the '-p' flag
    port_number = args.port

    # Creates a UDP socket
    with socket(AF_INET, SOCK_DGRAM) as server_socket:

        # Bind socket to the server
        server_socket.bind((ip_address, port_number))

        # Prints a message that the server is ready to receive
        print(f"The server is ready to receive")

        while True:
            # Receiving a message from a client
            client_message, client_address = server_socket.recvfrom(2048)


def start_client(args):
    # Defining the IP address using the '-I' flag
    ip_address = args.serverip

    # Defining the port number using the '-p' flag
    port_number = args.port

    # Create a UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)


# This is the main entry point of the program
if __name__ == '__main__':
    # Parses the command line arguments using the argparse module
    args = parse_args()
    
    # If the server flag is present, start the server
    if args.server:
        start_server(args)

    # If the client flag is present, start the client
    elif args.client:
        start_client(args)