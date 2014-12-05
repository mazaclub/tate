#!/usr/bin/env python
#
# Tate - lightweight Mazacoin client
# Copyright (C) 2012 thomasv@ecdsa.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import threading, time, Queue, os, sys, shutil
from util import user_dir, appdata_dir, print_error
from bitcoin import *


class Blockchain(threading.Thread):

    def __init__(self, config, network):
        threading.Thread.__init__(self)
        self.daemon = True
        self.config = config
        self.network = network
        self.lock = threading.Lock()
        self.local_height = 0
        self.running = False
        # TODO Change for tate
        self.headers_url = ''#'http://headers.electrum.org/blockchain_headers'
        self.set_local_height()
        self.queue = Queue.Queue()
        self.chunk_size = 2016 # number of headers in a chunk

    
    def height(self):
        return self.local_height


    def stop(self):
        with self.lock: self.running = False


    def is_running(self):
        with self.lock: return self.running


    def run(self):
        self.init_headers_file()
        self.set_local_height()
        print_error( "blocks:", self.local_height )

        with self.lock:
            self.running = True

        while self.is_running():

            try:
                result = self.queue.get()
            except Queue.Empty:
                continue

            if not result: continue

            i, header = result
            if not header: continue
            
            height = header.get('block_height')

            if height <= self.local_height:
                continue

            if height > self.local_height + 50:
                if not self.get_and_verify_chunks(i, header, height):
                    continue

            if height > self.local_height:
                # get missing parts from interface (until it connects to my chain)
                chain = self.get_chain( i, header )

                # skip that server if the result is not consistent
                if not chain: 
                    print_error('e')
                    continue
                
                # verify the chain
                if self.verify_chain( chain ):
                    print_error("height:", height, i.server)
                    for header in chain:
                        self.save_header(header)
                else:
                    print_error("error", i.server)
                    # todo: dismiss that server
                    continue


            self.network.new_blockchain_height(height, i)


                    
            
    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)
        
        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height, chain)
            _hash = self.hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True



    def verify_chunk(self, index, hexdata):
        data = hexdata.decode('hex')
        height = index*self.chunk_size
        num = len(data)/80

        if index == 0:  
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*self.chunk_size-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

#        bits, target = self.get_target(index)

        for i in range(num):
            height = index*self.chunk_size + i
            bits, target = self.get_target(height)
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            assert bits == header.get('bits')
            assert int('0x'+_hash,16) < target

            self.save_header(header, height)
            previous_header = header
            previous_hash = _hash 

#        self.save_chunk(index, data)
        print_error("validated chunk %d"%height)

        

    def header_to_string(self, res):
        s = int_to_hex(res.get('version'),4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')),4) \
            + int_to_hex(int(res.get('bits')),4) \
            + int_to_hex(int(res.get('nonce')),4)
        return s


    def header_from_string(self, s):
        hex_to_int = lambda s: int('0x' + s[::-1].encode('hex'), 16)
        h = {}
        h['version'] = hex_to_int(s[0:4])
        h['prev_block_hash'] = hash_encode(s[4:36])
        h['merkle_root'] = hash_encode(s[36:68])
        h['timestamp'] = hex_to_int(s[68:72])
        h['bits'] = hex_to_int(s[72:76])
        h['nonce'] = hex_to_int(s[76:80])
        return h

    def hash_header(self, header):
        return rev_hex(Hash(self.header_to_string(header).decode('hex')).encode('hex'))

    def path(self):
        return os.path.join( self.config.path, 'blockchain_headers')

    def init_headers_file(self):
        filename = self.path()
        if os.path.exists(filename):
            return
        
        try:
            import urllib, socket
            socket.setdefaulttimeout(30)
            print_error("downloading ", self.headers_url )
            urllib.urlretrieve(self.headers_url, filename)
            print_error("done.")
        except Exception:
            print_error( "download failed. creating file", filename )
            open(filename,'wb+').close()

    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(index*self.chunk_size*80)
        h = f.write(chunk)
        f.close()
        self.set_local_height()

    def save_header(self, header, height=None):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        if height is None: height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()
        self.set_local_height()


    def set_local_height(self):
        name = self.path()
        if os.path.exists(name):
            h = os.path.getsize(name)/80 - 1
            if self.local_height != h:
                self.local_height = h

    def roll_back_to_last_chunk(self):
        name = self.path()
        if os.path.exists(name):
            f = open(name,'rb+')
            f.seek((self.local_height/self.chunk_size)*80)
            f.truncate()
            f.close()
        self.set_local_height()

    def read_header(self, block_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name,'rb')
            f.seek(block_height*80)
            h = f.read(80)
            f.close()
            if len(h) == 80:
                h = self.header_from_string(h)
                return h 

    def bits_to_target(self, bits):
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))
        return target

    def target_to_bits(self, target):
        MM = 256*256*256
        c = ("%064X"%target)[2:]
        i = 31
        while c[0:2]=="00":
            c = c[2:]
            i -= 1

        c = int('0x'+c[0:6],16)
        if c >= 0x800000:
            c /= 256
            i += 1

        new_bits = c + MM * i
        return new_bits


    def get_target_v1(self, block_height, chain=None):
        # params
        nTargetTimespan = 8 * 60
        nTargetSpacing = 120
        interval = nTargetTimespan / nTargetSpacing # 4
        nAveragingInterval = interval * 20 # 80
        nAveragingTargetTimespan = nAveragingInterval * nTargetSpacing # 9600
        nMaxAdjustDown = 20
        nMaxAdjustUp = 15
        nMinActualTimespan = nAveragingTargetTimespan * (100 - nMaxAdjustUp) / 100
        nMaxActualTimespan = nAveragingTargetTimespan * (100 + nMaxAdjustDown) / 100


        if chain is None:
            chain = []  # Do not use mutables as default values!

# btc        max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000
        if block_height == 0: return 0x1e0ffff0, max_target

        # Start diff
        start_target = 0x00000003FFFF0000000000000000000000000000000000000000000000000000
        if block_height < nAveragingInterval: return 0x1d03ffff, start_target

        last = self.read_header(block_height-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == block_height-1:
                    last = h


        # Only change on each interval
        if not block_height % interval == 0:
            return self.get_target_v1(block_height-1, chain)


        # first = go back by averagingInterval
        first = self.read_header((block_height-1)-(nAveragingInterval-1))
        if first is None:
            for fh in chain:
                if fh.get('block_height') == (block_height-1)-(nAveragingInterval-1):
                    first = fh

  
        nActualTimespan = last.get('timestamp') - first.get('timestamp')
        nActualTimespan = max(nActualTimespan, nMinActualTimespan)
        nActualTimespan = min(nActualTimespan, nMaxActualTimespan)

        bits = last.get('bits') 
        # convert to bignum
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))

        # new target
        new_target = min( max_target, (target * nActualTimespan)/nAveragingTargetTimespan )
        
        # convert it to bits
        c = ("%064X"%new_target)[2:]
        i = 31
        while c[0:2]=="00":
            c = c[2:]
            i -= 1

        c = int('0x'+c[0:6],16)
        if c >= 0x800000: 
            c /= 256
            i += 1

        new_bits = c + MM * i
        return new_bits, new_target

    def get_target_dgw3(self, block_height, chain=None):
        if chain is None:
            chain = []

        last = self.read_header(block_height-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == block_height-1:
                    last = h

        # params
        BlockLastSolved = last
        BlockReading = last
        BlockCreating = block_height
        nActualTimespan = 0
        LastBlockTime = 0
        PastBlocksMin = 24
        PastBlocksMax = 24
        CountBlocks = 0
        PastDifficultyAverage = 0
        PastDifficultyAveragePrev = 0
        bnNum = 0

        max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        if BlockLastSolved is None or block_height-1 < PastBlocksMin:
            return 0x1e0ffff0, max_target
        for i in range(1, PastBlocksMax + 1):
            CountBlocks += 1

            if CountBlocks <= PastBlocksMin:
                if CountBlocks == 1:
                    PastDifficultyAverage = self.bits_to_target(BlockReading.get('bits'))
                else:
                    bnNum = self.bits_to_target(BlockReading.get('bits'))
                    PastDifficultyAverage = ((PastDifficultyAveragePrev * CountBlocks)+(bnNum)) / (CountBlocks + 1)
                PastDifficultyAveragePrev = PastDifficultyAverage

            if LastBlockTime > 0:
                Diff = (LastBlockTime - BlockReading.get('timestamp'))
                nActualTimespan += Diff
            LastBlockTime = BlockReading.get('timestamp')

            BlockReading = self.read_header((block_height-1) - CountBlocks)
            if BlockReading is None:
                for br in chain:
                    if br.get('block_height') == (block_height-1) - CountBlocks:
                        BlockReading = br

        bnNew = PastDifficultyAverage
        nTargetTimespan = CountBlocks * 120

        nActualTimespan = max(nActualTimespan, nTargetTimespan/3)
        nActualTimespan = min(nActualTimespan, nTargetTimespan*3)

        # retarget
        bnNew *= nActualTimespan
        bnNew /= nTargetTimespan

        bnNew = min(bnNew, max_target)

        new_bits = self.target_to_bits(bnNew)
        return new_bits, bnNew

    def get_target(self, block_height, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        DiffMode = 1
        if block_height >= 100000: DiffMode = 2

        if DiffMode == 1: return self.get_target_v1(block_height, chain)
        elif DiffMode == 2: return self.get_target_dgw3(block_height, chain)
        
        return self.get_target_dgw3(block_height, chain)


    def request_header(self, i, h, queue):
        print_error("requesting header %d from %s"%(h, i.server))
        i.send_request({'method':'blockchain.block.get_header', 'params':[h]}, queue)

    def retrieve_request(self, queue):
        while True:
            try:
                ir = queue.get(timeout=1)
            except Queue.Empty:
                print_error('blockchain: request timeout')
                continue
            i, r = ir
            result = r['result']
            return result

    def get_chain(self, interface, final_header):

        header = final_header
        chain = [ final_header ]
        requested_header = False
        queue = Queue.Queue()

        while self.is_running():

            if requested_header:
                header = self.retrieve_request(queue)
                if not header: return
                chain = [ header ] + chain
                requested_header = False

            height = header.get('block_height')
            previous_header = self.read_header(height -1)
            if not previous_header:
                self.request_header(interface, height - 1, queue)
                requested_header = True
                continue

            # verify that it connects to my chain
            prev_hash = self.hash_header(previous_header)
            if prev_hash != header.get('prev_block_hash'):
                print_error("reorg")
                self.roll_back_to_last_chunk()
#                self.request_header(interface, height - 1, queue)
#                requested_header = True
                return None

            else:
                # the chain is complete
                return chain


    def get_and_verify_chunks(self, i, header, height):

        queue = Queue.Queue()
        min_index = (self.local_height + 1)/self.chunk_size
        max_index = (height + 1)/self.chunk_size
        n = min_index
        while n < max_index + 1:
            print_error( "Requesting chunk:", n )
            i.send_request({'method':'blockchain.block.get_chunk', 'params':[n]}, queue)
            r = self.retrieve_request(queue)
            try:
                self.verify_chunk(n, r)
                n = n + 1
            except Exception:
                print_error('Verify chunk failed!')
                n = n - 1
                if n < 0:
                    return False

        return True

