from client import *
from server import *
from header import *
from application import *

# Her må vi opprette three way handshake 
    # Bruker flaggene som ligger i header for å sende SYN, ACK

# Three way handshake
def handshake_client(client_socket): 

    # Client mottar data fra server
    tuple = client_socket.recvfrom(1472)
    while tuple:
        data = tuple[0]
        address = tuple[1]

        # Sjekke pakkens header
        header_from_data = data[:12]
        seq, ack, flags, win = parse_header (header_from_data)
        syn, ack, fin = parse_flags(flags)
        #print(f'Dette er det jeg vil se på: Syn: {syn} Ack: {ack} fin: {fin}')

        # Hvis header har aktivert SYN-ACK flagg
        if flags == 12:
            ACK_packet = create_packet(0, 0, 4, 64000, b'')
            client_socket.send(ACK_packet)
            print('Nå har clienten sendt ACK')
            return


def handshake_server(flags, server_socket, address):
    # Sjekker om vi har mottatt SYN-flagg fra client
    if flags == 8:
        # Lager en SYN ACK pakke
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)
        print('Nå har vi server sendt SYN ACK')


# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements
