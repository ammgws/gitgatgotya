#!/usr/bin/env python3

# standard library
import datetime as dt
import logging
import os
import os.path
from configparser import ConfigParser
from pathlib import Path
from time import sleep
# third party
import click
import requests
from hangoutsclient import HangoutsClient

APP_NAME = 'gitgatgotya'


def create_dir(ctx, param, directory):
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    return directory


@click.command()
@click.option(
    '--config-path',
    type=click.Path(),
    default=os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), APP_NAME),
    callback=create_dir,
    help='Path to directory containing config file. Defaults to XDG config dir.',
)
@click.option(
    '--cache-path',
    type=click.Path(),
    default=os.path.join(os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), APP_NAME),
    callback=create_dir,
    help='Path to directory to store logs and such. Defaults to XDG cache dir.',
)
@click.option('--steam-id', '-i', help='SteamID of the user to check.')
@click.option('--api-key', '-k', help='Steam Web API key')
def main(config_path, cache_path, steam_id, api_key):
    """Sends a message via Hangouts if the Steam friend is currently playing a game."""
    configure_logging(cache_path)

    # TODO: see if can get click to load config file as fallback
    # See default_map (Context Defaults) or click-configfile
    # api_key = config.get('Hangouts', 'refresh_token')
    config_file = os.path.join(config_path, 'steam.ini')
    config = ConfigParser()
    config.read(config_file)
    logging.debug('Using config file: %s', config_file)
    hangouts_client_id = config.get('Hangouts', 'client_id')
    hangouts_client_secret = config.get('Hangouts', 'client_secret')
    hangouts_token_file = os.path.join(cache_path, 'hangouts_cached_token')
    if not os.path.isfile(hangouts_token_file):
        Path(hangouts_token_file).touch()

    # Get currently played game, if any
    url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&format=json&steamids={steam_id}'
    r = requests.get(url)
    if r.status_code == 200:
        current_game = r.json()['response']['players'][0].get('gameextrainfo')
        if current_game:
            message = f'Hope you are enjoying {current_game}'
        else:
            logging.info('Not gaming at the moment.')
            return

    hangouts = HangoutsClient(hangouts_client_id, hangouts_client_secret, hangouts_token_file)
    if hangouts.connect():
        hangouts.process(block=False)
        sleep(5)  # need time for Hangouts roster to update
        hangouts.send_to_all(message)
        hangouts.disconnect(wait=True)
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
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    # Lower requests module's log level so that OAUTH2 details aren't logged
    logging.getLogger('requests').setLevel(logging.WARNING)
    # Quieten SleekXMPP output
    # logging.getLogger('sleekxmpp.xmlstream.xmlstream').setLevel(logging.INFO)


if __name__ == '__main__':
    main()
