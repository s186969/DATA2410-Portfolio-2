from client import *
from server import *
from header import *
from application import *

# Her må vi opprette three way handshake 
    # Bruker flaggene som ligger i header for å sende SYN, ACK


def handshake_server(flags, server_socket, address):
    if flags == 8:
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)
        print(f'Nå har vi sendt SYN ACK {SYN_ACK_packet}')
        #Her har vi mottatt SYN-flagg
        #Opprett en pakke med SYN-ACK 
        #Send pakken tilbake til client
    
    #elif flags == 4:
        #Her har vi mottatt ACK-flagg

    #else:
        #feilmelding

# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements