#!/usr/bin/env python

import sys
import logging 
logging.basicConfig(level=logging.DEBUG)
sys.path.append('gen-py')

from blockServer import BlockServerService
from blockServer.ttypes import *
from shared.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.server import TServer
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class BlockServerHandler():

    def __init__(self, configpath):
        # Initialize using config file, intitalize state etc
        self.block_table = {}
	self.port = 0
	return

    def hasBlock(self, hash):
        # Chack if there is a block in server
	print "Called hasBlock on: "
	print hash
	out = hasBlockResponse()
	out.status = hasBlockResponseType.OK
        if hash in self.block_table:
            print "exit OK"
	    return out
        else:
            out.status = hasBlockResponseType.MISSING
        print "exit MISSING"
	return out

    def storeBlock(self, hashBlock):
        # Input:   struct hashBlock
	#              -> string hash
	#              -> binary block
	#              -> string status
	# 
	# Output:  struct response
	#              -> responseType message
	#                  -> OK or ERROR
	#
	# Store hash block, called by client during upload
        
	print "Called storeBlock"
        # Unpack hashBlock
        hash = hashBlock.hash
        
        # Create an empty response
        out = response()
        out.message = responseType.OK

	# Check block is in memory
	if hash in self.block_table:
            # Data already in memory
            return out
        else:
            # Add it to memory
            self.block_table[hash] = hashBlock 
            return out
    

    def getBlock(self, hash):
        # Retrieve block using hash, called by client during download
        #
        # Input:    string hash
	# Output:   struct hashBlock
        print "Returning block: ", hash
	return self.block_table[hash] 

    def deleteBlock(self, hash):
        # Delete the particular hash : block pair
        pass

    def readServerPort(self):
        # In this function read the configuration file and get the port number for the server
        return self.port

    # Add your functions here

# Add additional classes and functions here if needed


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Invocation <executable> <config_file>"
        exit(-1)

    print "Processing Configuration File"
    config_path = sys.argv[1]
    conf_info = []
    with open(config_path) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    for line in content:
        a = line.split(':')
        conf_info.append(int(a[1]))
    block_port = conf_info.pop(-1)
    print "Initializing block server"
    handler = BlockServerHandler(config_path)
    # Retrieve the port number from the config file so that you could strt the server
    #port = handler.readServerPort()
    # Define parameters for thrift server
    processor = BlockServerService.Processor(handler)
    transport = TSocket.TServerSocket(port=block_port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    # Create a server object
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    print "Starting server on port: ", block_port

    # START TEST CODE
    tmp = response()
    tmp.message = responseType.ERROR
    print tmp
    # END TEST CODE





    try:
        server.serve()
    except (Exception, KeyboardInterrupt) as e:
        print "\nExecption / Keyboard interrupt occured: ", e
        exit(0)
