# Description:
# Imports the necessary libraries
# header: This module contains the functions for creating and reading the header.
# client: This module contains the client functions.
# server: This module contains the server functions.
# drtp: This module contains the drtp layer functions.
# argparse: This module makes it easy to write user-friendly command-line interfaces.
# sys: This module provides access to some variables used or maintained by the Python interpreter and to functions that interact strongly with the interpreter.
# ipaddress: This module provides factory functions to conveniently create IP addresses and networks of different types.
from header import *
from client import *
from server import *
from drtp import *
import argparse
import sys
import ipaddress

# Description:
# This function will parse the command-line arguments
# Arguments:
# None
# Returns:
# args: The parsed command-line arguments
def parse_args():
    # Defines and parses the command-line argument
    parser = argparse.ArgumentParser(description = 'Reliable Data Transfer Protocol Application')
    
    # '-s' flag: Enables the server mode
    parser.add_argument('-s', '--server', action = 'store_true', help = "Enables server mode")

    # '-c' flag: Enables the client mode
    parser.add_argument('-c', '--client', action = 'store_true', help = "Enables client mode")

    # '-i' flag: Sets the IP address of the server that the client will connect to. Default value is '127.0.0.1'
    parser.add_argument('-i', '--serverip', type= str, default = '127.0.0.1', help = "Selects the IP address of server")

    # '-p' flag: Sets the port number that the server will listen on or the client will connect to. The default value is 8088
    parser.add_argument('-p', '--port', type = int, default = 8088, help = "Selects the port number")

    # '-f' flag: Sets the file to be transfered in the client.
    parser.add_argument('-f', '--filename', type = str, help = "Selects the file to be transfered")

    # '-r' flag: Sets the reliable method for the transfer
    parser.add_argument('-r', '--reliablemethod', type = str, help = "Selects a reliable method for the transfer. Choose either saw (Stop and Wait), gbn (Go-Back-N) or sr (Selective-Repeat)")

    # -'t' flag: Sets the test case for the program
    parser.add_argument('-t', '--testcase', type = str, help = "Selects a test case to run the program. Choose either skip_ack or loss")

    # -'w' flag: Sets the window size for Go-Back-N and Selective-Repeat
    parser.add_argument('-w', '--windowsize', type = int, default = 3, help = "Selects a window size for Go-Back-N and Selective-Repeeat")

    # '-b' flag: Sets the timeout to four times round-trip time
    parser.add_argument('-b', '--bonus', action = 'store_true', help = "Selects the timeout to four times round-trip time")
    
    # Parsing the command-line arguments
    args = parser.parse_args()

    # Checks conditions for flags
    validate_args(args)

    # Returns the parsed command-line arguments
    return args

# Description:
# This function will validate the command-line arguments
# Arguments:
# args: The parsed command-line arguments
# Returns: None
def validate_args(args):
    # Checks if both '-s' flag and '-c' flag are enabled at the same time
    if args.server and args.client:
        sys.exit("Error: You cannot run both server and client mode at the same time")

    # Checks if neither '-s' flag nor '-c' flag is enabled
    if not (args.server or args.client):
        sys.exit("Error: You must run either in server or client mode")

    # Checks if '-i' flag have a valid IP address
    try:
        ipaddress.ip_address(args.serverip)
    except ValueError:
        sys.exit("Error: Invalid IP address for '-i' flag")
    
    # Checks if the port number for the '-p' flag is between 1024 and 65535
    if args.port < 1024 or args.port > 65535:
        sys.exit("Error: Invalid value for '-p' flag. The port must be an integer in the range [1024, 65535]")

    # Checks if the '-f' flag is enabled
    if not args.filename and args.client is True:
        sys.exit("Error: You must select a file to transfer")

    # Checks if '-r' flag is enabled
    if not args.reliablemethod:
        sys.exit("Error: You must select a reliable method")

    # Checks if the format for the '-r' flag is correct
    if args.reliablemethod is not None and args.reliablemethod not in ["saw", "gbn", "sr"]:
        sys.exit("Error: Invalid value for '-r' flag. Format must be either saw, gbn or sr")

    # Checks if the format for the '-t' flag is correct
    if args.testcase is not None and args.testcase not in ["skip_ack", "loss"]:
        sys.exit("Error: Invalid value for '-t' flag. Format must be either skip_ack or loss")

    # Checks if server mode and test case 'loss' are enabled at the same time
    if args.testcase == "loss" and args.server:
        sys.exit("Error: Test case 'loss' cannot be run in server mode")

    # Checks if client mode and test case 'skip_ack' are enabled at the same time
    if args.testcase == "skip_ack" and args.client:
        sys.exit("Error: Test case 'skip_ack' cannot be run in client mode")

    # Checks if 'Stop and wait' and test case 'loss' are enabled at the same time
    if args.testcase == "loss" and args.reliablemethod == "saw":
        sys.exit("Error: Stop and wait cannot be run with test case 'loss'")

    # Checks if the value for the '-w' flag is between 2 and 15
    if args.windowsize < 2 or args.windowsize > 15:
        sys.exit("Error: Invalid value for '-w' flag. The window size must be a integer between 2 and 15")
              
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