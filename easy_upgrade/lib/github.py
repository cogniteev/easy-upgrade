
from datetime import datetime
import logging
import os
import os.path as osp
import stat

import requests

from .. api import (
    Fetcher,
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
    def __init__(self, provider, name, config):
        self.organization, self.repository = name.split('/', 1)
        super(GitHubRelease, self).__init__(provider, name, config)
        self.with_prerelease = self.get('with-prerelease', False)
        self.with_draft = self.get('with-draft', False)

    @property
    def pkg_name(self):
        return self.repository

    def get_releases(self):
        url = "{root}/repos/{org}/{repo}/releases".format(
            root=GITHUB_ROOT_API,
            org=self.organization,
            repo=self.repository
        )
        response = requests.get(url, auth=self.provider.basic_auth)
        response.raise_for_status()
        return response.json()

    def get_latest_release(self):
        result = None
        release_date = None

        releases = self.get_releases()
        for release in releases:
            if not self.with_prerelease and release['prerelease']:
                continue
            elif not self.with_draft and release['draft']:
                continue
            elif release_date is None:
                release_date = parse_date(release['published_at'])
                result = release
            else:
                date = parse_date(release['published_at'])
                if date > release_date:
                    release_date = date
                    result = release
        return result


class GitHubProvider(ReleaseProvider):
    def __init__(self, name, top_config, release_cls=GitHubRelease):
        super(GitHubProvider, self).__init__(name, top_config, release_cls)
        self.basic_auth = self.get('basic-auth')
        if self.basic_auth:
            self.basic_auth = tuple(self.basic_auth.split(':', 1))


class GitHubAsset(Fetcher):
    providers = 'github'
    name = 'asset'

    def candidate_version(self):
        if not getattr(self, 'grelease', None):
            self.grelease = self.release.get_latest_release()
        if self.grelease is None:
            return None
        version = self.grelease['name']
        return version

    def fetch(self, output_directory):
        name = self.get('name')
        if name is not None:
            name = self.jinja_eval(name)
        getattr(self, 'grelease')
        assets = self.grelease.get('assets', [])
        if not any(assets):
            logging.warning("Could not find any asset in release")
        else:
            if name is not None:
                # FIXME implement additional filters...
                assets = filter(lambda a: a['name'] == name, assets)
        for asset in assets:
            self.download_asset(asset, output_directory)
        if not any(assets):
            raise Exception("Didn't find asset matching requirements")

    def download_asset(self, asset, output_directory):
        url = asset['browser_download_url']
        output_file = osp.join(output_directory, self['file'])
        dir_path = osp.dirname(output_file)
        if not osp.isdir(dir_path):
            os.makedirs(dir_path)
        response = requests.get(
            url,
            auth=self.provider.basic_auth,
            stream=True
        )
        response.raise_for_status()
        with open(output_file, 'wb') as ostr:
            for block in response.iter_content(1024):
                ostr.write(block)
        if asset['content_type'] in ['application/octet-stream']:
            st = os.stat(output_file)
            os.chmod(
                output_file, st.st_mode |
                stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )
