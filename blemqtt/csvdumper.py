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


import argparse
import csv
import datetime
import json
import re
import sys

HEADER = ["index", "timestamp", "source", "target", "value", "position"]


def counter():
    i = 0
    while True:
        yield i
        i = i + 1


def get_target(record):
    m = re.search(
        r"/(?P<target>([0-9A-F]{2}:){5}[0-9A-F]{2})/", record["topic"]
    )
    return m.group("target")


def main():

    parser = argparse.ArgumentParser(
        epilog=(
            "Use with something like: "
            "mosquitto_sub -F %j -h mqtt -t 'blemqtt/#'"
        )
    )

    parser.add_argument("-s", "--source", required=True)
    parser.add_argument("-p", "--position", required=True)
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("rw+", encoding="utf-8"),
        default=sys.stdout,
    )
    args = parser.parse_args()

    writer = csv.writer(args.output, delimiter=";")
    writer.writerow(HEADER)

    idx_g = counter()
    while True:

        line = args.file.readline()
        if not line:
            break

        record = json.loads(line)
        record["index"] = next(idx_g)
        record["source"] = args.source
        record["position"] = args.position
        record["timestamp"] = datetime.datetime.fromtimestamp(record["tst"])
        record["target"] = get_target(record)
        record["value"] = record["payload"]
        row = [record[k] for k in HEADER]

        writer.writerow(row)

    # records = (
    #     re.search(REGEXP, line.strip()) for line in args.file.readlines()
    # )
    # records = (x.groupdict() for x in records if x)

    # writer = csv.writer(args.output, delimiter=";")
    # writer.writerow(HEADER)

    # for idx, record in enumerate(records):
    #     record['index'] = idx
    #     record['source'] = args.source
    #     record['position'] = args.position
    #     row = [record[k] for k in HEADER]
    #     writer.writerow(row)

    # args.output.close()


if __name__ == "__main__":
    main()
