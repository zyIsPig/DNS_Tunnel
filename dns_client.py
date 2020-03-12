



import select


import pytun
import dns.message
import dns.name
import dns.query



import base64 as b64
import time
import queue
import socket


client_addr = '10.20.0.1'
dst_addr = '10.20.0.2'
mask = '255.255.255.0'
# server_addr = '120.78.166.34'
server_addr = '52.82.37.174'





port = 53
mtu = 130
query_root_name = 'group-30.cs305.fun'
label_len = 63


class client:
    def __init__(self):
        # this will not cover the last one using command +c
        self._tun = pytun.TunTapDevice(name='mytun', flags=pytun.IFF_TUN | pytun.IFF_NO_PI)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # speed is nessary
        self.speed=0.8
        self.tag=0
        self.sta=0
        self._tun.addr = client_addr
        self._tun.dstaddr = dst_addr
        self._tun.netmask = mask
        self._tun.mtu = mtu
        self._tun.persist(True)
        self._tun.up()

    def run(self):
        mtu = self._tun.mtu
        
        r = [self._tun, self._socket]
        w = []
        x = []
        sender_data = b''
        tun_data = b''
        data_last = time.time()
        while True:
         
            r, w, x = select.select(r, w, x)


            #print("get this 1")
            if self._tun in r:
                tun_data = self._tun.read(mtu)
            if self._socket in r:
                self.sta=time.time()
                self.tag=1
                sender_data, target_addr = self._socket.recvfrom(65500)
                data_response = dns.message.from_wire(sender_data)
                if data_response.answer:
                    txt_record = data_response.answer[0]
                    sender_data = b64.b64decode(str(txt_record.items[0]))
                else:
                    sender_data = b''

            if self._tun in w :
                #print("get this 2")

                self._tun.write(sender_data)
                sender_data = b''
            if self._socket in w or (time.time()-self.sta)>0.1:
                encoded_tun_data = b64.b64encode(tun_data)
                name_split = [str(encoded_tun_data[s:s + label_len], encoding='ascii')
                                for s in range(0, len(encoded_tun_data), label_len)]
                name_split.append(query_root_name)
                target_domain = '.'.join(name_split)


                name = dns.name.from_text(target_domain)

                query = dns.message.make_query(name, 'TXT')
                self._socket.sendto(
                    query.to_wire(), (server_addr, port))
                tun_data = b''

                #print("get this 3")

            r = []
            w = []
            self.tag=0
            if sender_data:
                w.append(self._tun)
            else:
                r.append(self._socket)
            if not tun_data:
                r.append(self._tun)
            now = time.time()
            print(now - data_last)
            if now - data_last > self.speed or tun_data:
                print(tun_data)
                w.append(self._socket)
                data_last = now


if __name__ == '__main__':


    server = client()

    server.run()
