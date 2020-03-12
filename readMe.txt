Configuration:
	cd to the dns_client.py and dns_server.py and use 
	sudo python3 dns_client.py/python3 dns_server.py to start the script, after the two steps, the tunnel is established. If you want to exit the script use control+c to exit and use sudo ip link set mytun down to shut down the tun. In my test, I use proxychains to do the proxy test. 
	
Principle:
	
	First establish two tuns in the client and server, and then configure them in a network. After the step when you send the packet to server in client, the packet will be captured by the tun in client. Then my tun will encode the packet by base64 and put it in the head of the query name separated by ".". Because the limit to the length of dns query name. We need to set the mtu small enough to ensure the packet is integrated. The dns_server will capture the packet which port number is 53 in tun. Then we use base64 to decode the message the get the packet client want to send to server end. The we use tun to write the packet to the kernel. The kernel will collect the ip fragment together and send back the response message to the tun. Then we need to encode the data by base64 and put it in the TXT in the dns response packet because it's big volume. So the query dns message should in TXT format. At last, the dns response message will be captured by the tun configured in client. That is the brief principle of dns tunnel, the detail and the optimizations have been stated in the presentation. 


Resource:
	python dns
	python base64
	pytun