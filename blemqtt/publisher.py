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


import logging
import queue
import socket
import threading

from paho.mqtt import client

_logger = logging.getLogger("blemqtt.publisher")


class Publisher(threading.Thread):
    def __init__(self, q, topic_prefix, host="localhost", *args, **kwargs):
        super().__init__()
        self.q = q
        self.topic_prefix = topic_prefix
        self.host = host
        self.mqtt = client.Client(*args, **kwargs)
        self.join_req = threading.Event()

    def connect(self):
        try:
            self.mqtt.connect(self.host)
            return
        except ConnectionRefusedError:
            _logger.error(
                f"Unable to connect to '{self.host}': connection refused"
            )
        except socket.gaierror as e:
            _logger.error(f"Unable to connect to '{self.host}': {e.strerror}")

        raise ConnectError()

    def publish(self, topic, value):
        if not self.mqtt.is_connected():
            self.connect()

        self.mqtt.publish(topic, value)

    def run(self):
        while True:
            try:
                ev = self.q.get(timeout=1)
            except queue.Empty:
                if self.join_req.is_set():
                    break
                continue

            address, key, value = ev
            topic = f"{self.topic_prefix}/{address}/{key}"
            try:
                self.publish(topic, value)
                _logger.debug(f"Published '{topic}'='{value}'")
            except ConnectError:
                pass

    def join(self, *args, **kwargs):
        self.join_req.set()
        super().join(*args, **kwargs)


class _BaseException(Exception):
    pass


class ConnectError(_BaseException):
    pass
