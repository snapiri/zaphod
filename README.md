# zaphod
Zaphod is a library for performing network protocols sanity testing and may be
used for security testing

## Usage
Currently there are testers for the implemented protocols that may be used as
 examples for using this library, and the implemented protocols may be used 
 as references to create more protocol handlers.

### Creating a new protocol handler
Each handler should inherit the `ProtocolHandler` class in the `base_handler`
 module. It should implement the following methods:
  * `get_protocol_name` - returns the name of the protocol it handles
  * `create_packet` - returns a binary data of new packet (ethernet and up) 
  for the relevan protocol
  * `bind_socket` - binds a socket for the relevant protocol that will be 
  used to send the packets
  * `close_resource` - any resource release needed before disposal

In addition, it should use the `register_callback` method to register the 
 method to parse the received packets, and `unregister_callback` when no more
 parsing is required. The parsing method should call the `_emit_results` 
 method to raise the errors to the registered clients.
 
### Quick start using the library
 * Create a `PacketReader`
 * Create all the required protocol handlers
 * Register a callback method to handle all the raised errors to the 
 protocol handlers
 * Set the relevant protocols to `learn` mode if wanted
 * Start the reader to start listening for incoming packets
 * Start creating and sending packets by the protocol handlers
 * Make sure to stop the reader before exiting the program 
 
 See the test code for examples

## Mechanism in a nutshell
The system is comprised of a single packet reader, and multiple protocol 
 handlers. Each protocol handler creates and sends packets to the network, and
 registers to the reader to accept the reply packets. Whenever a packet is 
 received, it is up to the protocol handler to parse it and verify its 
 integrity. If any issues are found, the handler uses callback method to send
  the issues to any mechanism that registered for them. 

The currently implemented protocol handlers (`DHCP` and `ARP`) support two 
 modes of operation:
 * static validation
 * learning

In the _**static validation**_, all the data that is valid for the reply
 packets is supplied in advance (e.g. DHCP server MAC address), and the 
 information is only verified against it.

In the second method, _**learning**_ mode, the protocol handler uses 
 the information in the reply packets to learn the valid replies, and uses 
 this information to verify the information when the learning is over.
