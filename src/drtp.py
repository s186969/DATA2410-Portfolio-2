from client import *
from server import *
from header import *
from application import *

# Her må vi opprette three way handshake 
    # Bruker flaggene som ligger i header for å sende SYN, ACK

# Three way handshake
def handshake_client(client_socket): 
    # Client starter med å sende SYN
    SYN_packet = create_packet(0, 0, 8, 64000, b'')
    client_socket.send(SYN_packet)
    print('Her sender clienten SYN')

    client_socket.settimeout(0.5) # Sjekk om tiden skal være like lang her
    
    try: 
        # Client mottar data fra server
        data = client_socket.recvfrom(1472)[0]
        
        while data:
            # Sjekke pakkens header
            seq, ack, flags = read_header(data)

            # Hvis header har aktivert SYN-ACK flagg
            if flags == 12:
                ACK_packet = create_packet(0, 0, 4, 64000, b'')
                client_socket.send(ACK_packet)
                print('Nå har clienten sendt ACK')
                return
            
    except:
        print('Connection timeout')


def handshake_server(flags, server_socket, address):
    # Sjekker om vi har mottatt SYN-flagg fra client
    if flags == 8:
        # Lager en SYN ACK pakke
        SYN_ACK_packet = create_packet(0, 0, 12, 64000, b'')
        server_socket.sendto(SYN_ACK_packet, address)
        print('Nå har server sendt SYN ACK')
    
    if flags == 4:
        # Server mottar ACK fra klient og er da klar for å motta datapakker
        return
        
def read_header(data):
    header_from_data = data[:12]
    seq, ack, flags, win = parse_header (header_from_data)
    return seq, ack, flags


# Gracefully close when the transfer is finished
    # Sender sends FIN-packet. Receiver sends an ACK når FIN er received.
    # Etter at receiver har sendt ACK så lukkes connection.


# Construct the packets and acknowledgements
