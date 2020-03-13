#!/usr/bin/python3

# Copyright (C) 2020 Shachar Snapiri
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

# nagios.py v0.0.1
# 13/3/2020

# Test different net protocols integrity.
# Written by Shachar Snapiri <shachar@snapiri.net>

# This plugin will try to verify the DHCP server(s), according to the
# supplied configuration. It will also validate the ARP resolution according
# to the same file.

import argparse
import sys
import time

from zaphod.common import config
from zaphod.common import logger
from zaphod.common import packet_reader
from zaphod.protocols import ARP
from zaphod.protocols import DHCP

TEST_SLEEP_TIME = 2

LOG = logger.get_logger(__name__)

options = argparse.ArgumentParser(usage='%prog server [options]',
                                  description='Test network integrity')
options.add_argument('-f', '--file', type=str, default='/etc/zaphod.conf',
                     help='Configuration file location '
                          '(default: /etc/zaphod.conf)')
options.add_argument('-t', '--timeout', type=int, default=10,
                     help='Socket timeout (default: 10)')
options.add_argument('-v', '--verbose', action='count', default=0,
                     help='Print verbose output')


dhcp_errors = None
arp_errors = None


def _set_log_level(verbose):
    if verbose > 2:
        logger.set_log_level(logger.DEBUG)
    elif verbose > 1:
        logger.set_log_level(logger.INFO)
    elif verbose > 0:
        logger.set_log_level(logger.WARN)
    else:
        logger.set_log_level(logger.ERROR)


class DhcpTester(object):
    def __init__(self, zaphod_config):
        self.config = zaphod_config.get_dhcp_config()
        self._errors = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def _dhcp_status_callback(errors):
        global dhcp_errors
        dhcp_errors = errors

    def test_dhcp(self):
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('DHCP Reader is not ready')
            return False
        dhcp_proto = DHCP.DHCPProto(reader,
                                    False,
                                    self.config['servers'],
                                    self.config['dhcp_ranges'],
                                    self.config['gateways'],
                                    self.config['dns_servers'])
        dhcp_proto.register_callback(self._dhcp_status_callback)
        dhcp_proto.set_timeout(10)
        reader.start_reader()
        packet = dhcp_proto.create_packet()
        dhcp_proto.send_packet(packet)
        time.sleep(TEST_SLEEP_TIME)
        reader.stop_reader()
        dhcp_proto.close()
        global dhcp_errors
        if dhcp_errors:
            for dhcp_error in dhcp_errors:
                print(f'{dhcp_error}')
            return False
        return True


class ArpTester(object):
    def __init__(self, zaphod_config):
        self.config = zaphod_config.get_arp_config()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def _arp_status_callback(errors):
        global arp_errors
        arp_errors = errors

    def test_arp(self):
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('ARP Reader is not ready')
            return False
        arp_proto = ARP.ARPProto(reader, False, self.config['resolvers'])
        arp_proto.register_callback(self._arp_status_callback)
        arp_proto.set_timeout(10)
        reader.start_reader()
        for item in self.config['resolvers'].keys():
            packet = arp_proto.create_packet(ip_address=item)
            arp_proto.send_packet(packet)
        time.sleep(TEST_SLEEP_TIME)
        reader.stop_reader()
        arp_proto.close()
        global arp_errors
        if arp_errors:
            for arp_error in arp_errors:
                print(f'{arp_error}')
            return False
        return True


def main():
    args = options.parse_args()
    _set_log_level(args.verbose)
    status = 0
    try:
        zaphod_config = config.Config(args.file)
    except IOError:
        LOG.error('Config file does not exist or not accessible')
        return 3
    with DhcpTester(zaphod_config) as tester:
        if not tester.test_dhcp():
            status = 1
    with ArpTester(zaphod_config) as tester:
        if not tester.test_arp():
            status = 1

    if not status:
        print('All tests succeeded')

    sys.exit(status)


if __name__ == '__main__':
    main()
