#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# Copyright (C) 2021 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from setuptools import setup


import datetime


setup(
    name="blemqtt",
    version="0.0.0." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    author="Luis López",
    author_email="luis@cuarentaydos.com",
    packages=["blemqtt"],
    scripts=[],
    url="https://github.com/ldotlopez/blemqtt",
    license="LICENSE.txt",
    description=("Bluetooth low-enegy MQTT bridge"),
    long_description=open('README.md').read(),
    long_description_content_type='text/x-markdown',
    install_requires=["dbus-python", "pygobject", "paho-mqtt"],
    entry_points={"console_scripts": ["blemqtt=blemqtt.__main__:main"]},
)
