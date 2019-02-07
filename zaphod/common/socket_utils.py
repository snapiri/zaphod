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

import netifaces

from zaphod.common import logger
LOG = logger.get_logger(__name__)


def create_socket(sock_name, iface_name):
    try:
        iface_bytes = iface_name.encode('utf-8')
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                             socket.IPPROTO_RAW)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, iface_bytes)
    except socket.error as msg:
        LOG.error('%s error initializing socket %s for iface: %s',
                  sock_name, iface_name)
        LOG.exception(msg)
        return None

    return sock


def get_iface_hw_mac(iface_name):
    if iface_name not in netifaces.interfaces():
        return None
    return netifaces.ifaddresses(iface_name)[netifaces.AF_LINK][0]['addr']


def get_iface_ip_address(iface_name):
    if iface_name not in netifaces.interfaces():
        return None
    return netifaces.ifaddresses(iface_name)[netifaces.AF_INET][0]['addr']
