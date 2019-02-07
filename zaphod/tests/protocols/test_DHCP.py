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


class TestDHCP:
    IFACE_NAME = 'eth0'

    def __init__(self):
        self.num_runs = 1
        self.allowed_servers = '11:22:33:44:55:66',
        self.allowed_dhcp_ranges = '10.0.0.0/24',
        self.allowed_gateways = '10.0.0.1',
        self.allowed_dns = '10.0.0.1', '8.8.8.8'

    def SetUp(self):
        pass

    def test_learn(self):
        print( "---- Learning Usecase ----")
        reader = packet_reader.PacketReader(self.IFACE_NAME)
        dhcp_proto = DHCP.DHCPProto(reader)
        dhcp_proto.register_callback(self.dhcp_status_callback)
        dhcp_proto.learn = True
        reader.start_reader()
        # We may send as many as we want
        for x in range(0, self.num_runs+1):
            print(x)
            packet = dhcp_proto.create_packet()
            dhcp_proto.send_packet(packet)
            time.sleep(5)
            if x == 0:
                print("Stop learning")
                dhcp_proto.learn = False
        reader.stop_reader()
        dhcp_proto.close()
        return True

    def test_static(self):
        print("---- Static Info Usecase ----")
        reader = packet_reader.PacketReader(self.IFACE_NAME)
        dhcp_proto = DHCP.DHCPProto(reader,
                                    self.allowed_servers,
                                    self.allowed_dhcp_ranges,
                                    self.allowed_gateways,
                                    self.allowed_dns)
        dhcp_proto.register_callback(self.dhcp_status_callback)
        reader.start_reader()
        packet = dhcp_proto.create_packet()
        dhcp_proto.send_packet(packet)
        time.sleep(5)
        reader.stop_reader()
        dhcp_proto.close()
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
    tester.SetUp()
    tester.test_learn()
    tester.test_static()
