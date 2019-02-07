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

from zaphod.common import socket_utils
from zaphod.common import logger
LOG = logger.get_logger(__name__)


class ProtocolHandler(object):
    def __init__(self,
                 packet_reader):
        self._packet_reader = packet_reader
        self._iface_name = self._packet_reader.iface_name
        self._iface_mac = socket_utils.get_iface_hw_mac(self._iface_name)
        self._callbacks = []
        self._socket = self._bind_socket()
        self.learn = False

    @staticmethod
    @abc.abstractmethod
    def get_protocol_name():
        pass

    @abc.abstractmethod
    def create_packet(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def _bind_socket(self):
        pass

    @abc.abstractmethod
    def _close(self):
        pass

    def close(self):
        self._close()
        if self._socket:
            self._socket.close()

    def send_packet(self, packet_to_send):
        self._socket.send(packet_to_send)

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def unregister_callback(self, callback):
        self._callbacks.remove(callback)

    def _register_handler(self, protocol, handler):
        self._packet_reader.register_protocol_packet_handler(protocol, handler)

    def _unregister_handler(self, protocol, handler):
        self._packet_reader.unregister_protocol_packet_handler(protocol,
                                                               handler)

    def _emit_results(self, errors):
        for callback in self._callbacks:
            try:
                callback(errors)
            except Exception as e:
                LOG.error('Exception in callback: %s', e)