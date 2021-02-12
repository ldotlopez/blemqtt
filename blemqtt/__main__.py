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

import queue
# from typing import List, Tuple
import signal
import threading

from .blescanner import BLEScanner
from .publisher import Publisher

try:
    import yaml
    import voluptuous as vol
except ImportError:
    import sys
    import warnings

    warnings.warn("voluptuous and pyyaml are required to use the command line interface")
    sys.exit(255)


CONFIG_SAMPLE = """
adapter: hci0

devices:
  - '00:11:22:33:44:55'
  - 'AA:BB:CC:DD:EE:FF'

mqtt:
  host: mqtt.local
  topic_prefix: 'blemqtt/0'
"""


def _exit(forever, s, f):
    forever.set()


Schema = vol.Schema(
    {
        vol.All("adapter"): str,
        vol.All("devices"): [str],
        vol.All("mqtt"): vol.Schema(
            {vol.Optional("host"): str, "topic_prefix": str},
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

        scanner = BLEScanner(
            q, adapter=config["adapter"], devices=config["devices"]
        )

        publisher = Publisher(q, topic_prefix=config["mqtt"]["topic_prefix"])
        publisher.connect(host=config["mqtt"]["host"])

        scanner.start()
        publisher.start()

        forever = threading.Event()
        signal.signal(signal.SIGINT, lambda s, f: _exit(forever, s, f))
        forever.wait()

        scanner.join()
        publisher.join()

    else:
        parser.print_help()
        sys.exit(255)


if __name__ == "__main__":
    main()
