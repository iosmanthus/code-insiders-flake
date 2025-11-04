#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.pygithub -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz

import github
import json
import os
import subprocess
import tempfile

from datetime import datetime
from github import Github
from urllib.request import urlretrieve

token = os.getenv('GITHUB_TOKEN')
github_repo = os.getenv('GITHUB_REPOSITORY')

release_time = datetime.now().strftime("%Y%m%d%H%M%S")
asset_name = 'code-insiders.tar.gz'

subprocess.run('git config user.name "github-actions[bot]"'.split())
subprocess.run(
    'git config user.email "github-actions[bot]@users.noreply.github.com'.
    split())


def make_meta(version: str, sha256: str) -> dict:
    return {
        'version':
        version,
        'sha256':
        sha256,
        'url':
        f'https://github.com/{github_repo}/releases/download/{release_time}/{asset_name}'
    }


def download_insiders(tmpdir: str) -> (dict, str):
    url = 'https://update.code.visualstudio.com/latest/linux-x64/insider'
    print('downloading latest code-insiders')
    filename, _ = urlretrieve(url, f'{tmpdir}/{asset_name}')
    sha256 = subprocess.run(
        ['nix-hash', '--flat', '--type', 'sha256', '--base32', filename],
        stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    subprocess.run(['tar', '-xzf', filename, '-C', tmpdir],
                   stdout=subprocess.PIPE)
    with open(tmpdir + '/VSCode-linux-x64/resources/app/package.json') as f:
        version = json.load(f)['version']

    return make_meta(version, sha256), filename


def read_local_meta(metafile: str) -> dict:
    with open(metafile, 'r') as f:
        return json.load(f)


def update_local_meta(metafile: str, meta: dict):
    with open(metafile, 'w') as f:
        json.dump(meta, f, indent=4)


def commit(metafile: str, message: str):
    subprocess.run(['git', 'add', metafile], stdout=subprocess.PIPE)
    subprocess.run(['git', 'commit', '-sm', message], stdout=subprocess.PIPE)
    subprocess.run(['git', 'push', 'origin', 'main'])


def create_github_release(local_artifact: str, metafile: str, meta: dict):
    g = Github(token)
    repo = g.get_repo(github_repo)

    print('creating release')
    release = repo.create_git_release(
        tag=f'{release_time}',
        name=meta['version'],
        message=f'snapshot of code-insiders at {release_time}',
        target_commitish='main',
        draft=False,
        prerelease=False)

    print('upload assets to GitHub Release')
    release.upload_asset(local_artifact, name=asset_name)

def update_flake_input(input: str):
    subprocess.run(['nix', 'flake', 'update', '--update-input', input])

def check():
    subprocess.run(['nix', 'flake', 'check'])

def main(metafile: str, tmpdir: str):
    remote_meta, local_file = download_insiders(tmpdir)
    local_meta = read_local_meta(metafile)
    if remote_meta['sha256'] == local_meta['sha256']:
        print('code-insiders is up to date')
        return

    update_local_meta(metafile, remote_meta)
    update_flake_input('nixpkgs')

    commit(
        metafile,
        f"update snapshot of code-insiders at {release_time} to {remote_meta['version']}"
    )

    create_github_release(local_file, metafile, remote_meta)


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmpdir:
        main('meta.json', tmpdir)
