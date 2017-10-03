#!/usr/bin/env python3

# standard library
import datetime as dt
import logging
import os
import os.path
from time import sleep
# third party
import click
import requests
from hangoutsclient import HangoutsClient


@click.command()
@click.option('--config_path', '-c',
              default=os.path.expanduser('~/.config/gitgatgotya'),
              type=click.Path(exists=True),
              help='path to directory containing config file.')
@click.option('--steam-id', '-i', help='SteamID of the user to check.')
@click.option('--api-key', '-k', help='Steam Web API key')
def main(config_path, steam_id, api_key):
    """
    Login to Hangouts, send generated message and disconnect.
    """
    configure_logging(config_path)

    config_file = os.path.join(config_path, 'gat_steam.ini')
    logging.debug('Using config file: %s', config_file)
    # TODO: see if can get click to load config file as fallback
    # See default_map (Context Defaults) or click-configfile
    # api_key = config.get('Hangouts', 'refresh_token')

    # Get currently played game, if any
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&format=json&steamids={steam_id}"
    r = requests.get(url)
    if r.status_code == 200:
        current_game = r.json()['response']['players'][0].get('gameextrainfo')
        if current_game:
            message = f"Hope you've enjoying {current_game}"
        else:
            return

    # Setup Hangouts bot instance, connect and send message
    hangouts = HangoutsClient(config_file)
    if hangouts.connect():
        hangouts.process(block=False)
        sleep(5)  # need time for Hangouts roster to update
        hangouts.send_to_all(message)
        hangouts.disconnect(wait=True)
        logging.info("Finished sending today's message.")
    else:
        logging.error('Unable to connect to Hangouts.')


def configure_logging(config_path):
    # Configure root logger. Level 5 = verbose to catch mostly everything.
    logger = logging.getLogger()
    logger.setLevel(level=5)

    log_folder = os.path.join(config_path, 'logs')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder, exist_ok=True)

    log_filename = 'steam_{0}.log'.format(dt.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss'))
    log_filepath = os.path.join(log_folder, log_filename)
    log_handler = logging.FileHandler(log_filepath)

    log_format = logging.Formatter(
        fmt='%(asctime)s.%(msecs).03d %(name)-12s %(levelname)-8s %(message)s (%(filename)s:%(lineno)d)',
        datefmt='%Y-%m-%d %H:%M:%S')
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    # Lower requests module's log level so that OAUTH2 details aren't logged
    logging.getLogger('requests').setLevel(logging.WARNING)
    # Quieten SleekXMPP output
    # logging.getLogger('sleekxmpp.xmlstream.xmlstream').setLevel(logging.INFO)


if __name__ == '__main__':
    main()
