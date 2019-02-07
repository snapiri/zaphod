# Copyright (C) 2017 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import atexit
import collections
import socket
import threading

from ryu.lib.packet import packet as ryu_packet

from zaphod.common import socket_utils
from zaphod.common import logger
LOG = logger.get_logger(__name__)

ETH_P_ALL = 0x0003


class PacketReader(object):
    def __init__(self, iface_name, read_timeout=5):
        self.iface_name = iface_name
        self._protocols = collections.defaultdict(list)
        self._lsocket = self._bind_lsock(read_timeout)
        self._event = threading.Event()
        self._orig_signal_handler = None
        self._reader_thread = None

    @property
    def is_ready(self):
        return self._lsocket is not None

    def _bind_lsock(self, read_timeout):
        sock = socket_utils.create_socket('L-socket', self.iface_name)
        if not sock:
            return None
        try:
            sock.bind((self.iface_name, ETH_P_ALL))
        except socket.error as msg:
            LOG.error('L-Socket binding failed')
            LOG.exception(msg)
            return None
        sock.settimeout(read_timeout)
        return sock

    def register_protocol_packet_handler(self, protocol, handler):
        self._protocols[protocol].append(handler)

    def unregister_protocol_packet_handler(self, protocol, handler):
        self._protocols[protocol].remove(handler)

    def _handle_packet_in(self, data):
        try:
            packet = ryu_packet.Packet(data)
        except Exception as e:
            LOG.error('Failed parsing packet.')
            LOG.exception(e)
            return

        for protocol, handlers in self._protocols.items():
            proto_packet = packet.get_protocol(protocol)
            if proto_packet:
                for handler in handlers:
                    try:
                        handler(packet)
                    except Exception as e:
                        LOG.exception(e)

    def _read_packets(self, event):
        while not event.isSet():
            try:
                data, sa_ll = self._lsocket.recvfrom(65535)
            except socket.timeout:
                return
            if sa_ll[2] == socket.PACKET_OUTGOING:
                # packet originated from the local host - Discard
                pass
            elif sa_ll[2] == socket.PACKET_HOST:
                # packet addressed to the local host - Got something
                self._handle_packet_in(data)

    def start_reader(self):
        if not self.is_ready:
            return
        self._reader_thread = threading.Thread(target=self._read_packets,
                                               args=(self._event,))
        atexit.register(self.stop_reader)
        self._reader_thread.start()

    def stop_reader(self):
        if self._reader_thread and self._reader_thread.is_alive():
            self._event.set()
            self._reader_thread.join()
            self._event.clear()
            self._reader_thread = None

    def close(self):
        self._lsocket.close()
