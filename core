from migen import *
from migen.genlib.fifo import *
from migen.genlib import roundrobin

from litex.soc.interconnect.csr import *

# Creates logic statement to set log message based on order of log_sigs
def priority_send(log_sigs, log_codes, message):
    statement = None
    for log_sig, log_code in zip(log_sigs, log_codes):
        if statement is not None:
            statement = statement.Elif(log_sig, log_num.eq(log_code))
        else:
            statement = If(log_sig, log_num.eq(log_code))
    self.comb += statement
          
# Creates logic statement to confirm log message based on order of log_sigs
def priority_confirm(log_sigs, log_codes, ready):          
    statement = None
    for log_sig, log_code in zip(log_sigs, log_codes):
        if statement is not None:
            statement = statement.Elif(log_sig, log_sig.eq(0))
        else:
            statement = If(log_sig, log_sig.eq(0))
    return If(ready, statement)
    
#def make_log_sig(code):
#    log_sig = Signal()
#    log_sigs.append(log_sig)
#    log_codes.append(code)
#    return log_sig
            
#def log_rising_edge(log_sig, track_sig):
#    track_edge = Signal()
#    self.sync += track_edge.eq(track_sig)
#    self.sync += If(track_sig & ~track_edge, log_sig.eq(1))
    
#def create_rising_edge_log_sig(code, track_sig):
#    log_sig = make_log_sig(code)
#    log_rising_edge(log_sig, track_sig)

class LoggingSystem(Module, AutoCSR):
    def __init__(self):
        self.readable = Signal()
        
        # # #
    
        self.messages = []
        self.readys = []
        self.requests = []
    
        self._log_csr = log_csr = CSRStatus(48, name='log_buffer')
        
        self.log_fifo = log_fifo = SyncFIFO(48, 50)
        self.submodules += log_fifo
        self.comb += [log_fifo.replace.eq(0)]
        
        # On log read, try to read from FIFO
        #self.sync += If(log_csr.we, 
        #                If(log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))
        #                .Else(log_csr.status.eq(-1), log_fifo.re.eq(0)))
        #self.sync += [If(log_csr.we & log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))
        #                .Else(If(log_csr.we, log_csr.status.eq(-1)), log_fifo.re.eq(0))]
                        
        self.comb += If(log_fifo.readable, log_csr.status.eq(log_fifo.dout)).Else(log_csr.status.eq(-1))
        self.comb += log_fifo.re.eq(log_csr.we)
        self.comb += self.readable.eq(log_fifo.readable)
                        
        # Read into empty CSR
        #self.sync += [If((log_csr.status == -1) & log_fifo.readable, log_csr.status.eq(log_fifo.dout), log_fifo.re.eq(1))]
        
    def get_log_port(self):
        message = Signal(48)
        ready = Signal()
        request = Signal()
        
        self.messages.append(message)
        self.readys.append(ready)
        self.requests.append(request)
        
        return message, ready, request
        
    def do_finalize(self):
        #Create Arbiter
        arbiter = roundrobin.RoundRobin(len(self.messages), roundrobin.SP_CE)
        self.submodules += arbiter
        
        self.comb += [self.log_fifo.din.eq(Array(self.messages)[arbiter.grant]),                            #Map arbiter grant to data in
                        arbiter.ce.eq(self.log_fifo.writable),                                              #Arbitrate if fifo is writable
                        self.log_fifo.we.eq(self.log_fifo.writable & Array(self.requests)[arbiter.grant]),  #Write if writable and request available
                        arbiter.request.eq(Cat(self.requests))]                                             #Map requests to arbiter requests
                        
        #self.sync += If((self._log_csr.status == -1) & Array(self.requests)[arbiter.grant], self._log_csr.status.eq(Array(self.messages)[arbiter.grant]))
                        
        for i, ready in enumerate(self.readys):
            self.comb += ready.eq((arbiter.grant == i) & self.log_fifo.writable)