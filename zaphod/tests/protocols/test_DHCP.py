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

import time

from zaphod.common import packet_reader
from zaphod.protocols import DHCP
from zaphod.tests import cli_parser


class TestDHCP:

    def __init__(self):
        self.config = cli_parser.CliParser().get_dhcp_config()

    def _single_run(self):
        packet = self.dhcp_proto.create_packet()
        self.dhcp_proto.send_packet(packet)
        time.sleep(5)

    def test_learn(self):
        print("---- Learning Usecase ----")
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('Reader is not ready')
            return False
        self.dhcp_proto = DHCP.DHCPProto(reader, self.config.get('passive'))
        self.dhcp_proto.register_callback(self.dhcp_status_callback)
        self.dhcp_proto.learn = True
        reader.start_reader()

        # Use first packet to learn
        self._single_run()
        print("Stop learning")
        self.dhcp_proto.learn = False
        self._single_run()
        reader.stop_reader()
        self.dhcp_proto.close()
        return True

    def test_static(self):
        print("---- Static Info Usecase ----")
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('Reader is not ready')
            return False
        self.dhcp_proto = DHCP.DHCPProto(reader,
                                         self.config.get('passive'),
                                         self.config['servers'],
                                         self.config['dhcp_ranges'],
                                         self.config['gateways'],
                                         self.config['dns_servers'])
        self.dhcp_proto.register_callback(self.dhcp_status_callback)
        reader.start_reader()
        self._single_run()
        reader.stop_reader()
        self.dhcp_proto.close()
        return True

    @staticmethod
    def dhcp_status_callback(dhcp_errors):
        if not dhcp_errors:
            print('Success!!!')
        else:
            print('**** Failed ****')
            print('-' * 60)
            for error in dhcp_errors:
                print('%s' % (error,))
            print('-' * 60)


if __name__ == '__main__':
    tester = TestDHCP()
    tester.test_learn()
    tester.test_static()
