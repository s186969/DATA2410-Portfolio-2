# DATA2410-Portfolio-2

OVERVIEW  
This is a simple file transfer application, Reliable Transport Protocol (DRTP), built on top of UDP. It consists of a client and a server that enable reliable data transfer of files. The application supports three reliability functions: Stop and Wait, Go-Back-N, and Selective Repeat.

PREREQUISITES  
- Python 3.x installed on your system
- A text editor or an Integrated Development Environment (IDE) for editing Python code  
  
USAGE  
To run the application, you can use the following command-line arguments:  
  
General format  
```
python3 application.py [mode] [flags]
```

Running in the server  
To run the server, use the following command:
```
python3 application.py -s -f [filename] -m [reliability_method] [options]
```

-s: Indicates running the server  
-f: Specifies the filename to receive  
-m: Specifies the reliability method to use (stop_and_wait, gbn, sr)  
-t: Optional flag for testing purposes (skip_ack)  

Example:  
```
python3 application.py -s -f Photo.jpg -m gbn
```

To skip an ack to trigger retransmission at the sender-side:  
```
python3 application.py -s -f Photo.jpg -m gbn -t skip_ack
```

Running the client  
To run the client, use the following command:
```
python3 application.py -c -f [filename] -r [reliability_method] [options]
```

-c: Indicates running the client  
-f: Specifies the filename to send  
-r: Specifies the reliability method to use (stop_and_wait, gbn, sr)  
-t: Optional flag for testing purposes (loss)  

Example:  
```
python3 application.py -c -f Photo.jpg -r gbn
```

To test packet_loss scenario:  
```
python3 application.py -c -f Photo.jpg -r gbn -t loss
```

Reliability methods  
Stop and Wait (stop_and_wait):  
The sender sends a packet and waits for an acknowledgment (ACK). If an ACK is received, it sends a new packet. If an ACK does not arrive, it waits for a timeout and resends the packet.  
  
Go-Back-N (gbn):  
The sender implements the Go-Back-N strategy using a fixed window size of 5 packets. If no ACK packet is received within a given timeout, all packets that have not been acknowledged are assumed to be lost and retransmitted.  
  
Selective Repeat (sr):  
Combines both Go-Back-N and Selective Repeat to optimize performance. In this method, packets that arrive out of order are placed in the correct position in the receive buffer, rather than being discarded.  
  
Additional notes  
- The DRTP header includes a 32-bit sequence number, a 32-bit acknowledgment number, a 16-bit flags field, and a 16-bit window field.  
- The server and client establish a connection using a three-way handshake, similar to TCP.  
- The connection is gracefully closed after the file transfer is complete.  