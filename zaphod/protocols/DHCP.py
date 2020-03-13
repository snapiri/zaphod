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

import random
import socket
import struct

import netaddr
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet as ryu_packet
from ryu.lib.packet import udp
from ryu.ofproto import ether

from zaphod.common import socket_utils
from zaphod.common import protocol_errors
from zaphod.protocols import base_handler
from zaphod.common import logger
LOG = logger.get_logger(__name__)

DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68

DHCP_TIME_SERVER_OPT = 4
DHCP_MTU_OPT = 26
DHCP_STATIC_ROUTE_OPT = 33


class DHCPProto(base_handler.ProtocolHandler):

    def __init__(self,
                 packet_reader,
                 passive_mode=False,
                 allowed_servers=(),
                 allowed_dhcp_ranges=(),
                 allowed_gateways=(),
                 allowed_dns_servers=()):
        super(DHCPProto, self).__init__(packet_reader, passive_mode)
        self._rand = random.Random()
        self._rand.seed()
        self._xid = 0
        self.address = None
        self.allowed_servers = [item.lower() for item in allowed_servers]
        self.allowed_dhcp_ranges = [netaddr.IPNetwork(net)
                                    for net in allowed_dhcp_ranges]
        self.allowed_gateways = [netaddr.IPAddress(addr)
                                 for addr in allowed_gateways]
        self.allowed_dns_servers = [netaddr.IPAddress(addr)
                                    for addr in allowed_dns_servers]
        self.client_name = b'dhcp-tester'
        self._register_handler(dhcp.dhcp, self._handle_dhcp_packet)

    @staticmethod
    def get_protocol_name():
        return 'DHCP'

    def create_packet(self):
        packed_params = struct.pack('!BBBBBB',
                                    dhcp.DHCP_SUBNET_MASK_OPT,
                                    DHCP_MTU_OPT,
                                    dhcp.DHCP_GATEWAY_ADDR_OPT,
                                    dhcp.DHCP_DNS_SERVER_ADDR_OPT,
                                    DHCP_TIME_SERVER_OPT,
                                    DHCP_STATIC_ROUTE_OPT)
        option_list = [
            dhcp.option(dhcp.DHCP_MESSAGE_TYPE_OPT,
                        struct.pack('!B', dhcp.DHCP_DISCOVER)),
            dhcp.option(dhcp.DHCP_HOST_NAME_OPT, self.client_name),
            dhcp.option(dhcp.DHCP_PARAMETER_REQUEST_LIST_OPT, packed_params),
        ]
        options = dhcp.options(option_list=option_list)
        self._xid = self._rand.randint(0, 0xffffffff)
        protocols = [
            ethernet.ethernet(
                    ethertype=ether.ETH_TYPE_IP,
                    dst='FF:FF:FF:FF:FF:FF',
                    src=self._iface_mac),
            ipv4.ipv4(
                dst='255.255.255.255',
                src='0.0.0.0',
                tos=0x10,  # IPTOS_LOWDELAY
                ttl=16,
                proto=socket.IPPROTO_UDP),
            udp.udp(
                src_port=DHCP_CLIENT_PORT,
                dst_port=DHCP_SERVER_PORT),
            dhcp.dhcp(
                op=dhcp.DHCP_BOOT_REQUEST,
                htype=1,
                hlen=6,
                hops=0,
                xid=self._xid,
                secs=0,
                ciaddr='0.0.0.0',
                yiaddr='0.0.0.0',
                chaddr=self._iface_mac,
                options=options)
        ]

        dhcp_pkt = ryu_packet.Packet(protocols=protocols)
        dhcp_pkt.serialize()
        return dhcp_pkt.data

    def bind_socket(self):
        sock = socket_utils.create_socket('Socket', self._iface_name)
        if not sock:
            return None
        try:
            sock.setsockopt(socket.SOL_SOCKET,
                            socket.SO_BROADCAST, 1)
            sock.bind((self._iface_name, DHCP_CLIENT_PORT))
        except socket.error as msg:
            LOG.error('Socket binding failed')
            LOG.exception(msg)
            return None
        return sock

    @staticmethod
    def _get_dhcp_message_type_opt(dhcp_packet):
        for opt in dhcp_packet.options.option_list:
            if opt.tag == dhcp.DHCP_MESSAGE_TYPE_OPT:
                return ord(opt.value)

    def _handle_server_identifier_opt(self, value, dhcp_errors):
        val1, = struct.unpack('!I', bytes(value))
        address = netaddr.IPAddress(val1, 4)
        LOG.debug('Server identifier: %s', address)
        # TODO: Check if this IP is allowed

    def _handle_gateway_address_opt(self, value, dhcp_errors):
        val1, = struct.unpack('!I', bytes(value))
        address = netaddr.IPAddress(val1, 4)
        LOG.debug('Gateway address: %s', address)
        if not self._check_allowed_gateway(address):
            dhcp_errors.append(
                protocol_errors.InvalidGatewayIPAddress(self.__class__,
                                                        address))

    def _handle_dns_servers_opt(self, value, dhcp_errors):
        val_bytes = bytes(value)
        data_len = len(val_bytes)
        for start in range(0, data_len, 4):
            val1, = struct.unpack('!I', bytes(value)[start:start + 4])
            address = netaddr.IPAddress(val1, 4)
            LOG.debug('DNS Server: %s', address)
            if not self._check_allowed_dns(address):
                dhcp_errors.append(
                    protocol_errors.InvalidDnsServer(self.__class__, address))

    def _handle_subnet_mask_opt(self, value, dhcp_errors):
        val1, = struct.unpack('!I', bytes(value))
        mask = netaddr.IPAddress(val1, 4)
        LOG.debug('Subnet mask: %s', mask)
        if not self._check_subnet_mask(mask):
            cidr = netaddr.IPNetwork('%s/%s' % (self.address, mask,)).cidr
            dhcp_errors.append(protocol_errors.InvalidNetwork(
                self.__class__, cidr))

    def _handle_mtu_opt(self, value, dhcp_errors):
        mtu, = struct.unpack('!H', value)
        LOG.debug('MTU: %d', mtu)
        # TODO(snapiri) Check MTU

    def _handle_static_route_opt(self, value, dhcp_errors):
        val_bytes = bytes(value)
        data_len = len(val_bytes)
        for start in range(0, data_len, 8):
            val1, val2 = struct.unpack('!II', bytes(value)[start:start + 8])
            dest = netaddr.IPAddress(val1, 4)
            gateway = netaddr.IPAddress(val2, 4)
            LOG.debug('Static route: %s through %s', dest, gateway, )
            if not self._check_allowed_gateway(gateway):
                dhcp_errors.append(protocol_errors.InvalidRoute(
                    self.__class__, dest, gateway))

    def _handle_dhcp_opt(self, tag, value, dhcp_errors):
        handlers = {
            dhcp.DHCP_SERVER_IDENTIFIER_OPT:
                self._handle_server_identifier_opt,
            dhcp.DHCP_GATEWAY_ADDR_OPT: self._handle_gateway_address_opt,
            dhcp.DHCP_DNS_SERVER_ADDR_OPT: self._handle_dns_servers_opt,
            dhcp.DHCP_SUBNET_MASK_OPT: self._handle_subnet_mask_opt,
            DHCP_MTU_OPT: self._handle_mtu_opt,
            DHCP_STATIC_ROUTE_OPT: self._handle_static_route_opt,
        }
        handler = handlers.get(tag)
        if handler:
            handler(value, dhcp_errors)
        else:
            LOG.debug('Not handler for DHCP option %s', tag)

    def _check_item_in_list(self, item_type, item, item_list):
        if item in item_list:
            return True
        if self.learn:
            LOG.debug('Learned %s: %s', item_type, item)
            item_list.append(item)
            return True
        if not item_list:
            return True
        return False

    def _check_allowed_server_mac(self, server_mac):
        return self._check_item_in_list('server MAC',
                                        server_mac.lower(),
                                        self.allowed_servers)

    def _check_allowed_address(self, addr):
        if not self.allowed_dhcp_ranges and not self.learn:
            return True
        for allowed_range in self.allowed_dhcp_ranges:
            if addr in allowed_range:
                return True
        # Learning is in the netmask...
        return False

    def _check_allowed_gateway(self, addr):
        return self._check_item_in_list('gateway', addr,
                                        self.allowed_gateways)

    def _check_allowed_dns(self, addr):
        return self._check_item_in_list('DNS', addr,
                                        self.allowed_dns_servers)

    def _check_subnet_mask(self, mask):
        net = netaddr.IPNetwork('%s/%s' % (self.address, mask,))
        return self._check_item_in_list('Network', net,
                                        self.allowed_dhcp_ranges)

    def _handle_dhcp_packet(self, packet):
        dhcp_errors = []
        ethernet_packet = packet.get_protocol(ethernet.ethernet)
        dhcp_packet = packet.get_protocol(dhcp.dhcp)

        LOG.debug('xid: %d', dhcp_packet.xid)

        # Verify xid only on active mode
        if not self._passive_mode and dhcp_packet.xid != self._xid:
            LOG.debug('Invalid xid (Got %d, expecting %d) - ignoring',
                      dhcp_packet.xid, self._xid)
            return

        dhcp_message_type = self._get_dhcp_message_type_opt(dhcp_packet)
        if dhcp_message_type == dhcp.DHCP_OFFER:
            source_mac = ethernet_packet.src
            dest_mac = ethernet_packet.dst
            LOG.debug('Source MAC is: %s', source_mac)
            LOG.debug('Dest MAC is: %s', dest_mac)
            if not self._check_allowed_server_mac(source_mac):
                dhcp_errors.append(protocol_errors.InvalidServerMAC(
                    self.__class__, source_mac))

            self.address = netaddr.IPAddress(dhcp_packet.yiaddr)
            LOG.debug('Got IP address %s', self.address)
            if not self._check_allowed_address(self.address):
                if not self.learn:
                    dhcp_errors.append(protocol_errors.InvalidIPAddress(
                        self.__class__, self.address))
            for opt in dhcp_packet.options.option_list:
                self._handle_dhcp_opt(opt.tag, opt.value, dhcp_errors)
        else:
            LOG.debug('DHCP message type %d not handled', dhcp_message_type)
        self._emit_results(dhcp_errors)

    def close_resource(self):
        self._unregister_handler(dhcp.dhcp, self._handle_dhcp_packet)
