#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et:

"""
    Purge transmission torrents with several criteria.
"""

from __future__ import (unicode_literals, absolute_import,
                        print_function, division)

import argparse
import logging

import arrow
import transmissionrpc
import yaml


LOG_FILE = '/home/user/scripts/transmicleaner.log'
logging.basicConfig(
    format='%(asctime)s :: %(levelname)s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M',
    filename=LOG_FILE,
    level=logging.INFO
)


def get_config():
    """Parse yaml"""
    with open("transmicleaner.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    return cfg


def get_torrents():
    """Retrieve torrents in transmission"""
    config = get_config()
    tc = transmissionrpc.Client(
        'localhost',
        user=config['user'],
        password=config['passwd'],
        rpc='/torrent/rpc')

    timer_60 = arrow.utcnow().replace(days=-60)
    timer_80 = arrow.utcnow().replace(days=-80)

    torrents = tc.get_torrents()
    for torrent in torrents:
        done = torrent.date_done
        #print(torrent.name, "===", torrent.date_done)
        if arrow.get(done) < timer_60 and torrent.ratio > 3:
            t_name = torrent.name.encode('utf-8')
            print("*" * 5, t_name, "(%s)" % done)
            if args.prune:
                logging.info(
                    "On supprime %s ### {'date':%s, 'ratio':%s}",
                    torrent.name,
                    done,
                    torrent.ratio
                )
                tc.remove_torrent(torrent.hashString, delete_data=True)
        elif arrow.get(done) < timer_80 and torrent.ratio < 3:
            if args.prune:
                msg = ("Ratio faible, mais 80+ jours. "
                       "On supprime %s ### {'date':%s, 'ratio':%s}")
                logging.info(msg, torrent.name, done, torrent.ratio)
                tc.remove_torrent(torrent.hashString, delete_data=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prune", help="remove old torrents",
                        action="store_true")
    args = parser.parse_args()

    get_torrents()
