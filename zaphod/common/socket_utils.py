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

import fcntl
import socket
import struct

from zaphod.common import logger
LOG = logger.get_logger(__name__)

SIOCGIFADDR = 0x8915
SIOCGIFHWADDR = 0x8927


def create_socket(sock_name, iface_name):
    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                             socket.IPPROTO_RAW)
    except socket.error as msg:
        LOG.error('%s creation error : %s', sock_name, msg)
        raise
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error as msg:
        LOG.error('%s error in setsockopt SO_REUSEADDR : %s', sock_name, msg)
        raise

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                        iface_name)
    except socket.error as msg:
        LOG.error('%s error in setsockopt SO_REUSEADDR : %s', sock_name, msg)
        raise

    return sock


def get_iface_hw_mac(iface_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), SIOCGIFHWADDR,
                       struct.pack('256s', iface_name[:15]))
    return ':'.join(['%02x' % ord(char) for char in info[18:24]])


def get_iface_ip_address(iface_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), SIOCGIFADDR,
                       struct.pack('256s', iface_name[:15]))
    return socket.inet_ntoa(info[20:24])
