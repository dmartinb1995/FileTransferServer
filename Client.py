#!/usr/bin/env python
import os
import sys
import hashlib

sys.path.append('gen-py')

# Thrift specific imports
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from metadataServer import MetadataServerService
from blockServer import BlockServerService
from shared.ttypes import *
from metadataServer.ttypes import *
from blockServer.ttypes import *

# Add classes / functions as required here
def start_client(block_port, serverport, fname, dirf, op):
    try:
        f = open(os.devnull, 'w')
	old = sys.stderr
	sys.stderr = f
        #print "Connecting to Metadata server...",
	transport = TSocket.TSocket('localhost', serverport)
        transport = TTransport.TBufferedTransport(transport)
	protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = MetadataServerService.Client(protocol)
        #print "SUCCESS"

        #print "Connecting to Block Server...",
	b_trans = TSocket.TSocket('localhost', block_port)
	b_trans = TTransport.TBufferedTransport(b_trans)
	b_proto = TBinaryProtocol.TBinaryProtocol(b_trans)
	b_client = BlockServerService.Client(b_proto)
	#print "SUCCESS"
	#b_trans.open()
        #b_client.hasBlock("test client")
	#b_trans.close()
	#client.ping()
	
        #print "Creating file"
        aFile = file()
        aFile.filename = fname
        aFile.version = 1;
        aFile.status = responseType.OK
        #print "Mode:	", op

        if op == "upload":
            tmp = separate_file(dirf, fname)
	    aFile.hashList = tmp[0]
            #print "	Sending file metadata..."
            transport.open()
            res = client.storeFile(aFile)
            transport.close()
            #print "	The following blocks will be sent"
            b_trans.open()
            for b_hash in res.hashList:
                #print b_hash
                out = hashBlock()
                out.hash = b_hash
                out.block = (tmp[2])[b_hash]
                b_client.storeBlock(out)
            b_trans.close()
            transport.open()
	    res = client.storeFile(aFile)
	    transport.close()
            if res.status != uploadResponseType.OK:	
	        print "ERROR"
		return 2
	
	# if op is get
        if op == "download":
            transport.open()
	    hashBlockList = list()
	    res = client.getFile(fname)
	    if res.status == responseType.ERROR:
	        print "ERROR"
		return 2
	    #print "The following blocks will be fetched:"
	    #for hb in res.hashList:
	    #    print "	", hb
            for hb in res.hashList:
	        b_trans.open()
		# chech block server has block
		res2 = b_client.hasBlock(hb)
		#print "	Checking block ", hb
		if res2.status == hasBlockResponseType.OK:
		    #print "		OK - appending to hashBlock list"
		    tmp = b_client.getBlock(hb)
		    hashBlockList.append(tmp)
                else:
		    #print "Block not in server"
		    print "ERROR"
		    return 2
		b_trans.close()
                bl = join(hashBlockList, dirf, fname)
	if op == "delete":
            transport.open()
	    res = client.deleteFile(aFile)
            if res.message != responseType.OK:
                print "ERROR"
		return 2
	    transport.close()
	#close transport
        print "OK"
	sys.stderr = old
    except:
        return 3
    return 1

def separate_file(dirf, file_name):
    full = dirf + "/" + file_name
    file_obj = open(full, 'rb')
    block_list = []
    hash_list = []
    out = {}
    while True:
        block = file_obj.read(4194304)
        if not block:
            break
	# PRocess block
        file_hash = hashlib.sha256(block).hexdigest()
        block_list.append(block)
        hash_list.append(file_hash)
	out[file_hash] = block
    file_obj.close()
    return (hash_list, block_list, out)

def parse_path(path):
    lp = list(path)
    out = ""
    if lp[0] == "/":
        del(lp[0])
    if len(lp) > 0:
        out = "".join(lp)
    out = os.path.abspath(out)
    return out

def join(blockList, dirf, fname):
    full = dirf + "/" + fname
    output = open(full, 'wb')
    for b in blockList:
        #print type(b.block)
	output.write(b.block)
    output.close()
    
if __name__ == "__main__":

    if len(sys.argv) < 5:
        print "Invocation : <executable> <config_file> <base_dir> <command> <filename>"
        exit(-1)
    conf_file_arg = sys.argv[1]
    base_dir_arg  = parse_path(sys.argv[2])
    command_arg   = sys.argv[3]
    filename_arg  = sys.argv[4]

    #print "The following arguments were received:"
    #print "    Configfile Arg:	", conf_file_arg
    #print "    Base Dir Arg:\n 	", base_dir_arg
    #print "    Command Arg:	", command_arg
    #print "    Filename Arg:	", filename_arg, "\n"
    
    #print "Processing Configuration File:"
    conf_info = []
    with open(conf_file_arg) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    for line in content:
        a = line.split(':')
        conf_info.append(int(a[1]))
	
    qty_meta = conf_info.pop(0)
    block_port = conf_info.pop(-1)
    meta_port_ls = conf_info
    #print "    Qty Meta:	", qty_meta
    #for port in meta_port_ls:
    #    print "    Meta Port:	", port
    #print "    Block Port:	", block_port

    #print "Starting client"
    
    res = start_client(block_port, meta_port_ls[0], filename_arg, base_dir_arg, command_arg)
    if res == 3:
        res2 = start_client(block_port, meta_port_ls[1], filename_arg, base_dir_arg, command_arg)
        if res2 == 3:
	    res3 = start_client(block_port, meta_port_ls[2], filename_arg, base_dir_arg, command_arg)
            if res3 == 3:
	        print "ERROR"
		
