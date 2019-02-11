# Copyright (C) 2019 Huawei Technologies Co., Ltd.
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

import argparse
import json


class Config(object):

    def __init__(self):
        parser = argparse.ArgumentParser(description='Zaphod test')
        parser.add_argument('-c', '--config', required=True,
                            help='Config file to use')
        args = parser.parse_args()
        with open(args.config) as json_file:
            self.data = json.load(json_file)

    def _get_component_config(self, component):
        cfg = self.data.get('common')
        cfg.update(self.data.get(component, dict()))
        return cfg

    def get_arp_config(self):
        return self._get_component_config('arp')

    def get_dhcp_config(self):
        return self._get_component_config('dhcp')
