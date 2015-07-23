
from datetime import datetime
import logging
import os.path as osp
import shutil
import tempfile
import urllib

import requests

from . api import (
    Action,
    Release,
    ReleaseProvider,
)

GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'
GITHUB_ROOT_API = "https://api.github.com"


def parse_date(date):
    if date.endswith('Z'):  # replace zulu abbreviation by UTC
        date = date[:-1] + 'UTC'
    return datetime.strptime(date, GITHUB_DATE_FORMAT)


class GitHubRelease(Release):
    def __init__(self, name, config):
        super(GitHubRelease, self).__init__(name, config)
        self.with_prerelease = self.get('with-prerelease', False)
        self.with_draft = self.get('with-draft', False)
        self.organization, self.repository = name.split('/', 1)

    def get_releases(self):
        url = "{root}/repos/{org}/{repo}".format(
            root=GITHUB_ROOT_API,
            org=self.organization,
            repo=self.repository
        )
        return requests.get(url).json()

    def get_latest_release(self):
        release = None
        release_date = None

        for release in self.get_releases(self):
            if not self.with_prerelease and release['prerelease']:
                continue
            elif not self.with_draft and release['draft']:
                continue
            elif release is None:
                release = release
                release_date = parse_date(release['published_at'])
            else:
                date = parse_date(release['published_at'])
                if date > release_date:
                    release = release
                    release_date = date
        return release


class GitHubProvider(ReleaseProvider):
    def __init__(self, config, top_key='github', release_cls=GitHubRelease):
        super(GitHubProvider, self).__init__(config, top_key, release_cls)


class GitHubAsset(Action):
    providers = 'github'
    name = 'asset'

    def __call__(self, config, release, provider, prev_result=None):
        self.temp_dir = None
        name = config.get('name')
        if name is not None:
            name = self.jinja_eval(name)
        project_release = release.get_latest_release()
        if project_release is None:
            logging.warning("Could not find any release")
        else:
            assets = project_release.get('assets', [])
            if not any(assets):
                logging.warning("Could not find any asset in release")
            else:
                if name is not None:
                    # FIXME add other filters...
                    assets = filter(lambda a: a['name'] == name, assets)
            if 'output-file' in config:
                if len(assets) > 1:
                    raise Exception("More than one asset candidate")
                elif len(assets) == 0:
                    raise Exception("No asset found")
                else:
                    paths = [
                        self.download_asset(
                            assets[0],
                            output_file=config['output-file']
                        )
                    ]
            elif 'output-dir' in config:
                paths = []
                for asset in assets:
                    paths.append(self.download_asset(
                        asset,
                        output_dir=config['output-dir']
                    ))
            return {
                'temp_dir': self.temp_dir,
                'files': paths
            }

    def download_asset(self, asset, output_dir=None, output_file=None):
        assert output_dir ^ output_file
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp()
        d = urllib.URLopener()
        if output_dir:
            output = self.jinja_eval(output_dir)
        else:
            output = self.jinja_eval(output_dir)
        url = asset['browser_download_url']
        d.retrieve(url, osp.join(self.temp_dir, output))
        return output

    def cleanup(self):
        temp_dir = getattr(self, 'temp_dir', None)
        if temp_dir:
            shutil.rmtree(temp_dir)
