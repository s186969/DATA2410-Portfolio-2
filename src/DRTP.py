from client import *
from server import *
from header import *
from application import *

# Her må vi opprette three way handshake 
    # Bruker flaggene som ligger i header for å sende SYN, ACK

#def handshake_client(client_socket):



#def handshake_server():
#    data_received = server_socket.recv(1472).decode()


# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements

