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

import socket

import netaddr
from ryu.lib.packet import ethernet, arp
from ryu.lib.packet import packet as ryu_packet
from ryu.ofproto import ether

from zaphod.common import protocol_errors
from zaphod.common import socket_utils
from zaphod.protocols import base_handler

from zaphod.common import logger
LOG = logger.get_logger(__name__)

ETH_P_ALL = 0x0003


class ARPProto(base_handler.ProtocolHandler):
    def __init__(self,
                 packet_reader,
                 known_addresses=None):
        super(ARPProto, self).__init__(packet_reader)
        if known_addresses:
            self.known_addresses = {netaddr.IPAddress(addr): mac.lower()
                                    for addr, mac in known_addresses.items()}
        else:
            self.known_addresses = {}
        self._register_handler(arp.arp, self._handle_arp_packet)

    @staticmethod
    def get_protocol_name():
        return 'ARP'

    def create_packet(self, ip_address):
        iface_ip = socket_utils.get_iface_ip_address(self._iface_name)
        protocols = [
            ethernet.ethernet(
                    ethertype=ether.ETH_TYPE_ARP,
                    dst='FF:FF:FF:FF:FF:FF',
                    src=self._iface_mac),
            arp.arp_ip(arp.ARP_REQUEST,
                       self._iface_mac,
                       iface_ip,
                       '00:00:00:00:00:00',
                       '%s' % (ip_address,))
        ]

        arp_pkt = ryu_packet.Packet(protocols=protocols)
        arp_pkt.serialize()
        return arp_pkt.data

    def _bind_socket(self):
        sock = socket_utils.create_socket('Socket', self._iface_name)
        try:
            sock.setsockopt(socket.SOL_SOCKET,
                            socket.SO_BROADCAST, 1)
        except socket.error as msg:
            LOG.error('Socket error in setsockopt SO_BROADCAST : %s', msg)
            raise
        try:
            sock.bind((self._iface_name, socket.SOCK_RAW))
        except socket.error as msg:
            LOG.error('Socket binding failed : %s', msg)
            raise
        return sock

    def _check_mac_match(self, answer_ip, answer_mac):
        known_mac = self.known_addresses.get(answer_ip)
        if known_mac:
            result = (known_mac == answer_mac)
            if not result:
                LOG.debug('Got bad MAC %s for IP: %s, expecting %s',
                          answer_mac, answer_ip, known_mac)
            return result
        if self.learn:
            LOG.debug('Learned MAC %s for IP %s', answer_mac, answer_ip)
            self.known_addresses[answer_ip] = answer_mac
        else:
            LOG.debug('Unknown ARP %s: %s - ignoring', answer_mac, answer_ip)
        return True

    def _handle_arp_packet(self, packet):
        arp_errors = []
        arp_packet = packet.get_protocol(arp.arp)
        if arp_packet.opcode == arp.ARP_REPLY:
            if not arp_packet.dst_mac.lower() == self._iface_mac:
                # This will usually happen when the destination is broadcast
                arp_errors.append(
                    protocol_errors.InvalidMAC(self.__class__,
                                               arp_packet.dst_mac))
            answer_ip = netaddr.IPAddress(arp_packet.src_ip)
            answer_mac = arp_packet.src_mac.lower()
            LOG.debug('Got MAC %s for IP %s', answer_mac, answer_ip)
            if not self._check_mac_match(answer_ip, answer_mac):
                arp_errors.append(
                    protocol_errors.InvalidARP(self.__class__,
                                               answer_ip, answer_mac))
        else:
            LOG.debug('ARP opcode type %d not handled', arp_packet.opcode)
        self._emit_results(arp_errors)

    def _close(self):
        self._unregister_handler(arp.arp, self._handle_arp_packet)
