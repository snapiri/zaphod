# Copyright (c) 2018 Huawei
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

# THIS FILE IS MANAGED BY THE GLOBAL REQUIREMENTS REPO - DO NOT EDIT
import setuptools


setuptools.setup(name='zaphod',
                 version='0.0.1',
                 description='Network protocol verifier',
                 author='Shachar Snapiri',
                 author_email='shachar.snapiri@huawei.com',
                 license='Apache2',
                 packages=['zaphod'],
                 install_requires=[
                     'ryu>=4.24',
                     'netaddr>=0.7.18',
                     'netifaces>=0.10.9',
                 ],
                 classifiers=[
                     'Topic:: System:: Networking',
                     'Intended Audience:: Developers',
                     'Intended Audience:: Information Technology',
                     'License:: OSI Approved:: Apache Software License',
                     'Operating System:: POSIX:: Linux',
                     'Programming Language:: Python',
                     'Programming Language:: Python:: 2',
                     'Programming Language:: Python:: 2.7',
                     'Programming Language:: Python:: 3',
                     'Programming Language:: Python:: 3.6',
                     'Programming Language:: Python:: 3.7',
                 ],
                 )
