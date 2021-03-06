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
import platform
import queue
import re
import signal
import threading

from .publisher import Publisher
from .scanner import Scanner

try:
    import yaml
    import voluptuous as vol
except ImportError:
    import sys
    import warnings

    warnings.warn(
        "voluptuous and pyyaml are required to use the command line interface"
    )
    sys.exit(255)

_logger = logging.getLogger("blemqtt")


CONFIG_SAMPLE = """
nodename: raspberrypi

adapter: hci0

devices:
  - '00:11:22:33:44:55'
  - 'AA:BB:CC:DD:EE:FF'

scan_interval: 60

rssi_value_on_missing: -100

mqtt:
  host: mqtt.local
  topic_prefix: 'blemqtt'
"""


def _exit(forever, s, f):
    forever.set()


def validate_word(w):
    m = re.search(r"^[a-z0-9]+$", w, re.IGNORECASE)
    if m:
        return w
    else:
        raise vol.Invalid("This word is invalid.")


def validate_bt_address(addr):
    m = re.search(r"^([a-f0-9]{2}:){5}[a-f0-9]{2}$", addr, re.IGNORECASE)
    if m:
        return addr.upper()
    else:
        raise vol.Invalid("This address is invalid.")


def rssi_value_on_missing_val(x):
    if x is None:
        return x

    try:
        return int(x)
    except (ValueError, TypeError) as e:
        raise vol.Invalid("rssi_value_on_missing must be None or int") from e


def validate_scan_interval(x):
    if x < 15:
        _logger.warning(f"Scan interval must be at least 15s (current: {x})")

    return max(x, 15)


Schema = vol.Schema(
    {
        # socket.gethostname requires an active network connection.
        vol.Required("nodename", default=platform.node()): validate_word,
        vol.All("adapter"): validate_word,
        vol.All("devices"): [validate_bt_address],
        vol.All("scan_interval", default=60): lambda x: max(15, int(x)),
        vol.Optional(
            "rssi_value_on_missing", default=None
        ): rssi_value_on_missing_val,
        vol.All("mqtt"): vol.Schema(
            {
                vol.Required("host", default="localhost"): str,
                vol.Required("topic_prefix", default="blemqtt"): validate_word,
            },
            extra=vol.ALLOW_EXTRA,
        ),
    }
)


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--print-config-sample", action="store_true", dest="dump_config"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=argparse.FileType("r", encoding="utf-8"),
    )

    args = parser.parse_args()
    if not args.dump_config and not args.config:
        parser.print_help()
        sys.exit(255)

    if args.dump_config:
        print(CONFIG_SAMPLE)
        sys.exit(0)

    elif args.config:
        config = Schema(yaml.load(args.config, Loader=yaml.Loader))

        q = queue.Queue()

        scanner = Scanner(
            q,
            adapter=config["adapter"],
            devices=config["devices"],
            scan_interval=config["scan_interval"],
            rssi_value_on_missing=config["rssi_value_on_missing"],
        )

        publisher = Publisher(
            q,
            topic_prefix=(
                f"{config['mqtt']['topic_prefix']}/{config['nodename']}"
            ),
            host=config["mqtt"]["host"],
        )

        scanner.start()
        publisher.start()

        forever = threading.Event()
        signal.signal(signal.SIGINT, lambda s, f: _exit(forever, s, f))
        signal.signal(signal.SIGTERM, lambda s, f: _exit(forever, s, f))
        forever.wait()

        scanner.join()
        publisher.join()

    else:
        parser.print_help()
        sys.exit(255)


if __name__ == "__main__":
    main()
