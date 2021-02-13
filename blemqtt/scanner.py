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


import datetime
import functools
import logging
import threading
import time
from typing import List

import dbus
from gi.repository import GLib

_logger = logging.getLogger("blemqtt.scanner")

BLUEZ_NAME = "org.bluez"

DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
BLUEZ_ADAPTER1_IFACE = "org.bluez.Adapter1"

BLUEZ_ADAPTER_PATH = "/org/bluez/{adapter}"
BLUEZ_DEVICE1_IFACE = "org.bluez.Device1"


class Scanner(threading.Thread):
    START_DISCOVERY_WAIT = 15
    SCAN_INTERVAL = 60
    LOWEST_RSSI = -100

    def __init__(self, q, *, adapter: str, devices: List[str]):
        super().__init__()
        self.q = q
        self.bus = dbus.SystemBus()
        self.adapter = adapter
        self.devices = devices or []
        self.join_req = threading.Event()
        self.loop = GLib.MainLoop()

    #
    # Thread stuff
    #
    def run(self):
        GLib.idle_add(add_return_value(self._scheduler, False))
        self.loop.run()

    def join(self, *args, **kwargs):
        self.join_req.set()
        super().join(*args, **kwargs)

    def _check_join_req(self):
        if self.join_req.is_set():
            self.loop.quit()

    #
    # Scheduler
    #
    def _scheduler(self):
        time_left, timestamp = calc_next_slot(
            self.SCAN_INTERVAL, self.START_DISCOVERY_WAIT + 1
        )

        # Schedule discovery starter
        GLib.timeout_add_seconds(
            time_left - self.START_DISCOVERY_WAIT,
            add_return_value(self._start_discovery, False),
        )

        # Schedule scan
        GLib.timeout_add_seconds(
            time_left,
            add_return_value(self._scan_devices, False),
        )

        # Schedule next cron
        GLib.timeout_add_seconds(
            time_left, add_return_value(self._scheduler, False)
        )

        dt = datetime.datetime.fromtimestamp(timestamp)
        _logger.debug(f"Next scan scheduled at {dt}")

    #
    # DBus stuff
    #
    def get_adapter1_iface(self) -> dbus.Interface:
        adapter_path = BLUEZ_ADAPTER_PATH.format(adapter=self.adapter)
        return get_interface(
            self.bus, BLUEZ_NAME, adapter_path, BLUEZ_ADAPTER1_IFACE
        )

    def _start_discovery(self):
        adapter1 = self.get_adapter1_iface()
        props = get_iface_properties_dict(adapter1)
        if not props["Discovering"]:
            _logger.debug(f"Start discovery on {self.adapter}")
            adapter1.StartDiscovery()

    def _stop_discovery(self):
        adapter1 = self.get_adapter1_iface()
        props = get_iface_properties_dict(adapter1)
        if props["Discovering"]:
            _logger.debug(f"Stop discovery on {self.adapter}")
            try:
                # This method fails if we are not the starters?
                adapter1.StopDiscovery()
            except dbus.DBusException:
                _logger.error("Unable to stop discovery")
                return

    def _scan_devices(self):
        _logger.debug(f"Scan devices on {self.adapter}")

        for address in self.devices:
            underscored_address = address.replace(":", "_")
            device_path = (
                f"/org/bluez/{self.adapter}/dev_{underscored_address}"
            )

            try:
                device1 = get_interface(
                    self.bus, BLUEZ_NAME, device_path, BLUEZ_DEVICE1_IFACE
                )
                props = get_iface_properties_dict(device1)

            except dbus.DBusException:
                props = {}

            self.q.put(
                (address, "RSSI", int(props.get("RSSI", self.LOWEST_RSSI)))
            )

        self._stop_discovery()


def get_interface(
    bus: dbus.Bus, objname: str, objpath: str, interface: str
) -> dbus.proxies.Interface:
    obj = bus.get_object(objname, objpath)
    iface = dbus.Interface(obj, interface)
    return iface


def get_properties(
    bus: dbus.Bus, objname: str, objpath: str
) -> dbus.proxies.Interface:
    props = get_interface(bus, objname, objpath, DBUS_PROPERTIES_IFACE)
    return props


def get_properties_dict(
    bus: dbus.Bus, objname: str, objpath: str, iface: str
) -> dbus.Dictionary:
    props = get_properties(bus, objname, objpath)
    return props.GetAll(iface)


def get_iface_properties_dict(iface: dbus.Interface) -> dbus.Dictionary:
    return dbus.Interface(iface, DBUS_PROPERTIES_IFACE).GetAll(
        iface.dbus_interface
    )


def add_return_value(fn, ret):
    @functools.wraps(fn)
    def _wrapper():
        fn()
        return ret

    return _wrapper


def calc_next_slot(secs, margin=0):
    now = int(time.mktime(time.localtime()))
    next_slot = (((now + margin) // secs) * secs) + secs

    return next_slot - now, next_slot


class UnknowDeviceError(Exception):
    pass
