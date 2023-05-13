# DATA2410 Portfolio 2
Reliable Transport Protocol (DRTP) is a simple file transfer application that is built on top of UDP. The main objective of this application is to transfer a JPG file to the destination where it will be named to *received_image.jpg*. The application consists of a client and a server that ensures reliable data transfer of files by establishing a connection using a three-way handshake. In addition, the application will utilise three reliable methods that a user can select to secure the transmission. Each packet in the transmission will consist of 1472 bytes, with 12 bytes of header and 1460 bytes of data. 

## Requirements  
- Python 3.6 or higher
  
## Installation
To install this application, you can download the script directly from GitHub or clone the repository to your local machine using the following command:

```
git clone https://github.com/s186969/DATA2410-Portfolio-2.git
```

Once the repository has been cloned, you can run the script in a topology using Python 3:

```
python3 application.py <arguments>
```

## Usage
To run the application, you can use the following command-line arguments:  

```
-s, --server          Enables server mode
-c, --client          Enables client mode
-i, --serverip        Selects the IP address of server
-p, --port            Selects port number
-f, --filename        Selects the file to be transfered
-r, --reliablemethod  Specifies the reliability method to use (saw, gbn, sr) 
-t, --testcase        Optional flag for testing purposes (skip_ack or loss)
-w, --windowsize      Sets a window size for Go-Back-N and Selective Repeeat (2-15)
-b, --bonus           Setting the timeout to four times round-trip time of former packet
```

The arguments are not set in positionals. You can set the order of the arguments as you wish.

Following arguments have a default value if they are not set:
```
-i, --serverip        127.0.0.1
-p, --port            8088
-w, --windowsize      3
```

For a full list of available options, use the -h flag:
```
python3 application.py -h
```

### Server mode
To run the tool in server mode, use the -s flag:
```
python3 application.py -s -i <ip_address> -p <port_number> -r <reliable_method>
```

### Client mode

To run the tool in client mode, use the -c flag:
```
python3 application.py -c -i <ip_address> -p <port_number> -f <name_name> -r <reliable_method>
```
**NOTE** Both server and client MUST use the same reliable_method.

### Reliable methods
The application supports three reliable methods: Stop and Wait, Go-Back-N, and Selective Repeat.

#### Stop and Wait
The sender sends a packet and waits for an acknowledgment (ACK). If an ACK is received, it sends a new packet. If an ACK does not arrive, it waits for a timeout and resends the packet.  

#### Go-Back-N
The sender uses a window to transmit multiple packets without waiting for individual acknowledgements. If no ACK packet is received within a given timeout, all packets that have not been acknowledged are assumed to be lost and retransmitted.  

#### Selective Repeat  
Similar to Go-Back-N by transmitting multiple packets in a window. The difference in this method is that the packets that arrive out of order are placed in a buffer, rather than being discarded.  

### Test cases
This application also supports two test cases to trigger retransmission: skip_ack and loss.

#### Skip_ack
The test case simulates a scenario where the acknowledgement is lost during the transmission from the server, forcing the client to retransmit the packet.

#### Loss
The test case aims to simulate a situation where a client sends a specific packet to the server, but it is lost during the transmission. This will also trigger retransmission.  

## Examples
#### Stop and Wait
To run the server on the local machine and listening on port number 8080 while using the method 'Stop and wait', input the following command:
```
python3 application.py -s -i 127.0.0.1 -p 8080 -r saw
```

Use the following command on the client side to transmit the image *bergen.jpg*:
```
python3 application.py -c -i 127.0.0.1 -p 8080 -r saw -f bergen.jpg
``` 

#### Go-Back-N
To use the method *Go-Back-N* with test case <code>skip_ack</code>, input the following command:
```
python3 application.py -s -i 127.0.0.1 -p 8080 -r gbn -t skip_ack
``` 

Use the following command on the client side:
```
python3 application.py -c -i 127.0.0.1 -p 8080 -r gbn -f bergen.jpg
```

#### Selective Repeat  
To use the method *Selective Repeat* with test case <code>loss</code>, input the following command:
```
python3 application.py -s -i 127.0.0.1 -p 8080 -r sr
``` 

Use the following command on the client side:
```
python3 application.py -c -i 127.0.0.1 -p 8080 -r sr -t loss -f bergen.jpg
```

#### Round-trip time
To use the round-trip time multiplied by four as the timeout in *Stop and Wait*, input the following command:
```
python3 application.py -s -i 127.0.0.1 -p 8080 -r saw
```
Use the following command on the client side:
```
python3 application.py -c -i 127.0.0.1 -p 8080 -r saw -f bergen.jpg -b
``` 
