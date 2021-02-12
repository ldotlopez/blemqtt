import functools
import logging
import threading
import time
from typing import List, Tuple

import dbus
from gi.repository import GLib

logging.basicConfig()
_LOGGER = logging.getLogger("blescanner")
_LOGGER.setLevel(logging.DEBUG)


BLUEZ_NAME = "org.bluez"

DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
BLUEZ_ADAPTER1_IFACE = "org.bluez.Adapter1"

BLUEZ_ADAPTER_PATH = "/org/bluez/{adapter}"
BLUEZ_DEVICE1_IFACE = "org.bluez.Device1"


class BLEScanner(threading.Thread):
    START_DISCOVERY_WAIT = 5
    SCAN_INTERVAL = 30
    LOWEST_RSSI = -100

    def __init__(self, q, *, adapter: str, devices: List[Tuple[str, str]]):
        super().__init__()
        self.q = q
        self.bus = dbus.SystemBus()
        self.adapter = adapter
        self.devices = devices or []
        self.join_req = threading.Event()
        self.loop = GLib.MainLoop()

    def run(self):
        GLib.idle_add(add_return_value(self._scan_devices, False))

        GLib.timeout_add_seconds(
            1, add_return_value(self._check_join_req, True)
        )
        GLib.timeout_add_seconds(
            self.SCAN_INTERVAL, add_return_value(self._scan_devices, True)
        )
        self.loop.run()

    def join(self, *args, **kwargs):
        self.join_req.set()
        super().join(*args, **kwargs)

    def _scan_devices(self):
        _LOGGER.debug(f"Scan devices on {self.adapter}")
        self._ensure_discovery()

        for address in self.devices:
            address2 = address.replace(":", "_")
            objpath = f"/org/bluez/{self.adapter}/dev_{address2}"
            try:
                props = get_properties_dict(
                    self.bus,
                    BLUEZ_NAME,
                    objpath,
                    BLUEZ_DEVICE1_IFACE,
                )
            except dbus.DBusException:
                props = {}

            self.q.put(
                (address, "RSSI", int(props.get("RSSI", self.LOWEST_RSSI)))
            )

    def _ensure_discovery(self):
        adapter_path = BLUEZ_ADAPTER_PATH.format(adapter=self.adapter)

        adapter1 = get_interface(
            self.bus, BLUEZ_NAME, adapter_path, BLUEZ_ADAPTER1_IFACE
        )
        props = get_properties_dict(
            self.bus, BLUEZ_NAME, adapter_path, BLUEZ_ADAPTER1_IFACE
        )

        if not props["Discovering"]:
            _LOGGER.debug("Start discovery on {self.adapter}")
            adapter1.StartDiscovery()
            time.sleep(self.START_DISCOVERY_WAIT)

    def _check_join_req(self):
        if self.join_req.is_set():
            self.loop.quit()


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


def add_return_value(fn, ret):
    @functools.wraps(fn)
    def _wrapper():
        fn()
        return ret

    return _wrapper


class UnknowDeviceError(Exception):
    pass
