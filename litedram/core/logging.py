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
                        
        self.comb += If(log_fifo.readable, log_csr.status.eq(log_fifo.dout)).Else(log_csr.status.eq(-1))
        self.comb += log_fifo.re.eq(log_csr.we)
        self.comb += self.readable.eq(log_fifo.readable)
                        
    def get_log_port(self):
        message = Signal(48)
        ready = Signal()
        request = Signal()
        
        self.messages.append(message)
        self.readys.append(ready)
        self.requests.append(request)
        
        return message, ready, request

    def log_on_rising_edge(self, log_sig):
        pass
        
    def do_finalize(self):
        #Create Arbiter
        arbiter = roundrobin.RoundRobin(len(self.messages), roundrobin.SP_CE)
        self.submodules += arbiter
        
        self.comb += [self.log_fifo.din.eq(Array(self.messages)[arbiter.grant]),                            #Map arbiter grant to data in
                        arbiter.ce.eq(self.log_fifo.writable),                                              #Arbitrate if fifo is writable
                        self.log_fifo.we.eq(self.log_fifo.writable & Array(self.requests)[arbiter.grant]),  #Write if writable and request available
                        arbiter.request.eq(Cat(self.requests))]                                             #Map requests to arbiter requests
                        
        for i, ready in enumerate(self.readys):
            self.comb += ready.eq((arbiter.grant == i) & self.log_fifo.writable)
