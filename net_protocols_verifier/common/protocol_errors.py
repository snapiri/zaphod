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

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseError(object):
    def __init__(self, module):
        self._module = module
        self._protocol_name = self._module.get_protocol_name()


class InvalidMAC(BaseError):
    def __init__(self, module, mac):
        super(InvalidMAC, self).__init__(module)
        self.mac = mac

    def __str__(self):
        return '%s: Invalid MAC address: %s' % (self._protocol_name, self.mac,)


class InvalidServerMAC(InvalidMAC):
    def __init__(self, module, mac):
        super(InvalidServerMAC, self).__init__(module, mac)

    def __str__(self):
        return '%s: Invalid Server MAC address: %s' % (
            self._protocol_name, self.mac,)


class InvalidIPAddress(BaseError):
    def __init__(self, module, ip_address):
        super(InvalidIPAddress, self).__init__(module)
        self.ip_address = ip_address

    def __str__(self):
        return '%s: Invalid IP Address: %s' % (self._protocol_name,
                                               self.ip_address,)


class InvalidServerIPAddress(InvalidIPAddress):
    def __init__(self, module, ip_address):
        super(InvalidServerIPAddress, self).__init__(module, ip_address)

    def __str__(self):
        return '%s: Invalid Server IP Address: %s' % (self._protocol_name,
                                                      self.ip_address,)


class InvalidGatewayIPAddress(InvalidIPAddress):
    def __init__(self, module, ip_address):
        super(InvalidGatewayIPAddress, self).__init__(module, ip_address)

    def __str__(self):
        return '%s: Invalid Gateway IP Address: %s' % (self._protocol_name,
                                                       self.ip_address,)


class InvalidDnsServer(InvalidIPAddress):
    def __init__(self, module, ip_address):
        super(InvalidDnsServer, self).__init__(module, ip_address)

    def __str__(self):
        return '%s: Invalid DNS Server: %s' % (self._protocol_name,
                                               self.ip_address,)


class InvalidRoute(InvalidGatewayIPAddress):
    def __init__(self, module, dest_ip, gateway_ip):
        super(InvalidRoute, self).__init__(module, gateway_ip)
        self.dest_ip = dest_ip

    def __str__(self):
        return '%s: Invalid Route: %s through %s' % (self._protocol_name,
                                                     self.dest_ip,
                                                     self.ip_address,)


class InvalidNetwork(BaseError):
    def __init__(self, module, ip_network):
        super(InvalidNetwork, self).__init__(module)
        self.ip_network = ip_network

    def __str__(self):
        return '%s: Invalid Server IP Network: %s' % (self._protocol_name,
                                                      self.ip_network,)


class InvalidARP(BaseError):
    def __init__(self, module, mac, ip):
        super(InvalidARP, self).__init__(module)
        self.mac = mac
        self.ip = ip

    def __str__(self):
        return '%s: Invalid ARP response: %s -> %s' % (self._protocol_name,
                                                       self.mac, self.ip,)
