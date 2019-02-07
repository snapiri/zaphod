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

import logging


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt = '%d/%m/%Y %H:%M:%S')

_loggers = {}

CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG


def set_log_level(level):
    for logger in _loggers.values():
        logger.setLevel(level)


def get_logger(name=None):
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
        _loggers[name].setLevel(logging.DEBUG)
        # _loggers[name].addHandler(logging.FileHandler('logs/' + name, 'w'))
    return _loggers[name]
