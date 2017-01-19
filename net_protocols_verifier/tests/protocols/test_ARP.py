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

from net_protocols_verifier.common import packet_reader
from net_protocols_verifier.protocols import ARP


class TestARP(object):
    IFACE_NAME = 'eth0'
    GW_ADDRESS = '10.0.0.1'

    def __init__(self):
        self.num_runs = 1
        self.known_hosts = {self.GW_ADDRESS: '11:22:33:44:55:66', }

    def SetUp(self):
        pass

    def test_learn(self):
        print("---- Learning Usecase ----")
        reader = packet_reader.PacketReader(self.IFACE_NAME)
        arp_proto = ARP.ARPProto(reader)
        arp_proto.register_callback(self.arp_status_callback)
        arp_proto.learn = True
        reader.start_reader()
        # We may send as many as we want
        for x in range(0, self.num_runs+1):
            print x
            packet = arp_proto.create_packet(ip_address=self.GW_ADDRESS)
            arp_proto.send_packet(packet)
            time.sleep(5)
            if x == 0:
                arp_proto.learn = False
        reader.stop_reader()
        arp_proto.close()
        return True

    def test_static(self):
        print("---- Static Info Usecase ----")
        reader = packet_reader.PacketReader(self.IFACE_NAME)
        arp_proto = ARP.ARPProto(reader, self.known_hosts)
        arp_proto.register_callback(self.arp_status_callback)
        reader.start_reader()
        packet = arp_proto.create_packet(ip_address=self.GW_ADDRESS)
        arp_proto.send_packet(packet)
        time.sleep(5)
        reader.stop_reader()
        arp_proto.close()
        return True

    @staticmethod
    def arp_status_callback(errors):
        if not errors:
            print('Success!!!')
        else:
            print('**** Failed ****')
            print('-' * 60)
            for error in errors:
                print('%s' % (error,))
            print('-' * 60)


if __name__ == '__main__':

    tester = TestARP()
    tester.SetUp()
    tester.test_learn()
    tester.test_static()
