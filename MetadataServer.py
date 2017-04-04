#!/usr/bin/env python
import time
import sys
import logging
sys.path.append('gen-py')
from timeout import timeout
# Thrift specific imports
from thrift import Thrift
from thrift.transport import TSocket
from thrift.server import TServer
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Protocol specific imports
from metadataServer import MetadataServerService
from blockServer import BlockServerService
from shared.ttypes import *
block_port = 1234
class MetadataServerHandler():

    def __init__(self, config_path, my_id):
        # Initialize block
        global block_port
	print "Other servers at: ", portList
        self.file_list = {}

	print "Connecting to Block Server", block_port
	self.transport = TSocket.TSocket('localhost', block_port)
	self.transport = TTransport.TBufferedTransport(self.transport)
	self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = BlockServerService.Client(self.protocol)

	return


    def getFile(self, filename):
        # Function to handle download request from file
        out = file()
	print "Client called getFile(", filename, ")"
	if filename in self.file_list:
	    print "OK - returning file info"
            return (self.file_list)[filename]
	else:
	    print "ERROR - file not in database"
            out.status = responseType.ERROR
	return out



    def storeFile(self, file):
        # Function to handle upload request
        print "Client called storeFile(", file.filename,")"

	# Add file to meta database
	#(self.file_list)[file.filename] = file

	(self.transport).open()
        missing_blocks = []     # list of missing blocks
        print file.hashList

	# Call block server on each hash to see if exists
        for hash_val in file.hashList:
            response = (self.client).hasBlock(hash_val)
            if response.status == hasBlockResponseType.MISSING:
                missing_blocks.append(hash_val)
	print "The following blocks are missing"
	out = uploadResponse()
	out.status = uploadResponseType.MISSING_BLOCKS
	if len(missing_blocks) == 0:
	    print "	[none]"
	    out.status = uploadResponseType.OK

	for b in missing_blocks:
            print "	", b
        (self.transport).close()
        if len(missing_blocks) == 0:
	    (self.file_list)[file.filename] = file
	    try:
	        #update other servers
		print "Updating others"
                print "Connecting to ", portList[0], " back up server"
    	        t2 = TSocket.TSocket('localhost', portList[0])
    	        t2 = TTransport.TBufferedTransport(t2)
    	        p2 = TBinaryProtocol.TBinaryProtocol(t2)
    	        c2 = MetadataServerService.Client(p2)
		t2.open()
		c2.updateFile(file)
		t2.close()

		print "Connecting to ", portList[1], " back up server"
    	        t3 = TSocket.TSocket('localhost', portList[1])
    	        t3 = TTransport.TBufferedTransport(t3)
    	        p3 = TBinaryProtocol.TBinaryProtocol(t3)
                c3 = MetadataServerService.Client(p3)
                t3.open()
		c3.updateFile(file)
		t3.close()

	    except:
	        pass
	# Compose response
	out.hashList  = missing_blocks


	return out

    def deleteFile(self, file):
        # Function to handle delete request from file
        print "Client called deleteFile( ", file.filename, ")"
	out = response()
        if file.filename in self.file_list:
            del (self.file_list)[file.filename]
            print "	Deleted file from meta database"
        else:
	    print "	File not in meta database"
        try:
	    print "Updating others"
	    print "Connecting to ", portList[0], " back up server"
    	    t2 = TSocket.TSocket('localhost', portList[0])
    	    t2 = TTransport.TBufferedTransport(t2)
    	    p2 = TBinaryProtocol.TBinaryProtocol(t2)
            c2 = MetadataServerService.Client(p2)
            t2.open()
            c2.updateDelete(file)
            t2.close()

	    print "Connecting to ", portList[0], " back up server"
            t3 = TSocket.TSocket('localhost', portList[1])
            t3 = TTransport.TBufferedTransport(t3)
            p3 = TBinaryProtocol.TBinaryProtocol(t3)
            c3 = MetadataServerService.Client(p3)
            t3.open()
            c3.updateDelete(file)
            t3.close()
	except:
	    pass
	out.message = responseType.OK
	return out

    def updateFile(self, file):
        print "Foreign Update: File"
	out = response()
	out.message = responseType.OK
	self.file_list[file.filename] = file

	return out

    def updateDelete(self, file):
        print "Foreign Update: Delete"
	out = response()
	out.message = responseType.OK
	if file.filename in self.file_list:
	    del (self.file_list)[file.filename]
	return out

    def readServerPort(self):
        # Get the server port from the config file.
        # id field will determine which metadata server it is 1, 2 or n
        # Your details will be then either metadata1, metadata2 ... metadatan
        # return the port
        pass

    # Add other member functions if needed



# Add additional classes and functions here if needed

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "Invocation <executable> <config_file> <id>"
        exit(-1)

    config_path = sys.argv[1]
    my_id = int(sys.argv[2])
    logging.basicConfig()

    print "Processing Configuration File:"
    conf_info = []
    with open(config_path) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    for line in content:
        a = line.split(':')
        conf_info.append(int(a[1]))

    # Start client to block server
    block_port = conf_info.pop(-1)
    qty_meta = conf_info.pop(0)
    port = conf_info.pop(my_id-1)
    global portList
    portList = conf_info

    print "Initializing metadata server"
    handler = MetadataServerHandler(config_path, my_id)
    #port = handler.readServerPort()
    # Define parameters for thrift server
    processor = MetadataServerService.Processor(handler)
    transport = TSocket.TServerSocket(port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    # Create a server object
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    print "Starting server on port : ", port


    try:
        server.serve()
    except (Exception, KeyboardInterrupt) as e:
        print "\nExecption / Keyboard interrupt occured: ", e
        exit(0)
