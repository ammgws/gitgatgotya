# python standard library
import os.path
from configparser import ConfigParser
# third party
import click
from github import Github


@click.command()
@click.option('--config_path', '-c',
              default=os.path.expanduser('~/.config/gitgatgotya'),
              type=click.Path(exists=True),
              help='path to directory containing config file.')
def main(config_path):
    # Read in config values
    config_file = os.path.join(config_path, 'config.ini')
    config = ConfigParser()
    config.read(config_file)
    oauth_token = config.get('General', 'oauth_token')
    target_username = config.get('General', 'target_username')

    g = Github(oauth_token)
    my_starred = g.get_user().get_starred()
    wyn_starred = g.get_user(target_username).get_starred()

    [g.get_user().add_to_starred(repo) for repo in wyn_starred if repo not in my_starred]


if __name__ == '__main__':
    main()
