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
from zaphod.protocols import ARP
from zaphod.tests import config


class TestARP(object):

    def __init__(self):
        self.config = config.Config().get_arp_config()

    def _single_run(self):
        for item in self.config['resolvers'].keys():
            packet = self.arp_proto.create_packet(ip_address=item)
            self.arp_proto.send_packet(packet)
        time.sleep(5)

    def test_learn(self):
        print("---- Learning Usecase ----")
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('Reader is not ready')
            return False
        self.arp_proto = ARP.ARPProto(reader, self.config.get('passive'))
        self.arp_proto.register_callback(self.arp_status_callback)
        self.arp_proto.learn = True
        reader.start_reader()
        # Use first packet to learn
        self._single_run()
        print("Stop learning")
        self.arp_proto.learn = False
        for x in range(0, self.config['runs']):
            print("Run number %d" % (x,))
            self._single_run()
        reader.stop_reader()
        self.arp_proto.close()
        return True

    def test_static(self):
        print("---- Static Info Usecase ----")
        reader = packet_reader.PacketReader(self.config['interface'])
        if not reader.is_ready:
            print('Reader is not ready')
            return False
        self.arp_proto = ARP.ARPProto(reader,
                                      self.config.get('passive'),
                                      self.config['resolvers'])
        self.arp_proto.register_callback(self.arp_status_callback)
        reader.start_reader()
        self._single_run()
        reader.stop_reader()
        self.arp_proto.close()
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
    tester.test_learn()
    tester.test_static()
