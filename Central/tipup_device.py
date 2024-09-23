class TipupDevice():
    def __init__(self, conn_handle, name, addr) -> None:
        self.connection_handle = conn_handle
        self.name = name
        self.address = addr
        self.io_characteristic = None
    
    def __str__(self):
        return f"[TipUp Device]: connection_handle={ self.connection_handle } name={ self.name } address={ self.addr }"