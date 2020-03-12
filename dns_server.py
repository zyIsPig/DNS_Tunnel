import sys


from queue import Queue
from queue import LifoQueue

import socket
import select

import pytun
import dns.message
import dns.name
import dns.query
import dns.resolver
import base64 as b64
import dns.rrset

server_addr = '10.20.0.2'
mask = '255.255.255.0'
mtu = 180
server_port = 53

class server_tun:
    def __init__(self):
       
        self._tun = pytun.TunTapDevice(name='mytun4', flags=pytun.IFF_TUN| pytun.IFF_NO_PI)

        self._tun.addr = server_addr
        self._tun.netmask = mask
        self._tun.mtu = mtu
        self._tun.persist(True)
        self._tun.up()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('', 53))
        self.data_queue = LifoQueue(65532)
        self.buffer_ip = Queue(65532)
        

    def recever(self):
        data, addr = self._socket.recvfrom(65523)
        pack_from_client = dns.message.from_wire(data)
        name = str(pack_from_client.question[0].name)
        name = name[:-20]
        data_recv = ''.join(name.split('.'))
        tun_bus_data = b64.b64decode(data_recv)

        self.data_queue.put((pack_from_client, addr))

        return tun_bus_data

    def run(self):

        mtu = self._tun.mtu
        r = [self._tun, self._socket]
        w = []
        x = []
        tun_bus_data = ''
        data_to_socket = ''
        target_addr = ()
        pack_from_client = None

        while True:
            r, w, x = select.select(r, w, x)
            if self._tun in r:
                data_to_socket = self._tun.read(mtu)
                
            if self._socket in r:
                tun_bus_data = self.recever()
                print(tun_bus_data)
            if self._tun in w:
                self._tun.write(tun_bus_data)
                tun_bus_data = ''
            if self._socket in w and not self.data_queue.empty():
                pack_from_client, target_addr = self.data_queue.get()
                response = dns.message.make_response(
                    pack_from_client, recursion_available=True)
                response.answer.append(dns.rrset.from_text(
                    pack_from_client.question[0].name, 30000, 1, 'TXT', str(b64.b64encode(data_to_socket), encoding='ascii')))
                self._socket.sendto(response.to_wire(), target_addr)
                data_to_socket = b''
            r = []
            w = []
            if tun_bus_data:
                w.append(self._tun)
            else:
                r.append(self._socket)

            if data_to_socket:
                w.append(self._socket)
            else:
                r.append(self._tun)


if __name__ == '__main__':
    server = server_tun()
    server.run()
