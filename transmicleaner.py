#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:

"""
    Purge transmission torrents with several criteria.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import logging
from pathlib import Path
import urllib.request

import pendulum
import transmission_rpc
import yaml

LOG_FILE = "/tmp/transmicleaner.log"
SCRIPT_DIR = Path(__file__).parent.absolute()
CFG_FILE = Path(SCRIPT_DIR / "transmicleaner.yml")

logging.basicConfig(
    format="%(asctime)s :: %(levelname)s :: %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    filename=LOG_FILE,
    level=logging.INFO,
)


def get_config():
    """Parse yaml"""
    with open(CFG_FILE, "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    return cfg


def get_torrents():
    """Retrieve torrents in transmission"""

    config = get_config()
    tc = transmission_rpc.Client(
        host="localhost",
        username=config["user"],
        password=config["passwd"],
        path="/torrent/rpc",
    )

    days_min = config.get("criteria").get("min_days")
    days_max = config.get("criteria").get("max_days")
    ratio_min = config.get("criteria").get("min_ratio")

    timer_min = pendulum.now("Europe/Paris").subtract(days=days_min)
    timer_max = pendulum.now("Europe/Paris").subtract(days=days_max)
    # print(timer_min)

    torrents = tc.get_torrents()
    for torrent in torrents:
        # Skip private tracker torrents to maintain good score
        if torrent.trackers and any(
            tracker in torrent.trackers[0].announce
            for tracker in ("generation-free.org/announce", "tracker.la-cale.space")
        ):
            logging.info(
                "Tracker privé, on ne touche pas au torrent %s",
                torrent.name,
            )
            continue

        done = str(torrent.added_date)
        if pendulum.parse(done) < timer_min and torrent.ratio > ratio_min:
            t_name = torrent.name  # .encode("utf-8")
            # print("*" * 5, t_name, "(%s)" % done)
            if args.prune:
                logging.info(
                    "On supprime %s ### {'date':%s, 'ratio':%s}",
                    torrent.name,
                    done,
                    torrent.ratio,
                )
                tc.remove_torrent(torrent.hashString, delete_data=True)
        elif pendulum.parse(done) < timer_max and torrent.ratio < ratio_min:
            if args.prune:
                logging.info(
                    "Ratio faible, mais %d+ jours. On supprime %s ### {'date':%s, 'ratio':%s}",
                    days_max,
                    torrent.name,
                    done,
                    torrent.ratio,
                )
                tc.remove_torrent(torrent.hashString, delete_data=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--prune", help="remove old torrents", action="store_true"
    )
    args = parser.parse_args()

    try:
        get_torrents()
        # FIXME refactor in order not to call get_config twice
        config = get_config()
        urllib.request.urlopen(config["hc_url"])
    except:
        raise
