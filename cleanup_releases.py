#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.pygithub -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/2d293cb.tar.gz
# 2025-11-30

import os
from datetime import datetime, timezone

from github import Auth, Github, GitRelease

token = os.getenv('GITHUB_TOKEN')
github_repo = os.getenv('GITHUB_REPOSITORY')

auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(github_repo)

def purge_release(release: GitRelease):
    print(f'Purging release: {release.tag_name}, created at: {release.created_at}, age: {(datetime.now(timezone.utc) - release.created_at).days} days')
    assets = release.get_assets()
    for asset in assets:
        print(f'Deleting asset: {asset.name}')
        asset.delete_asset()
    print(f'Deleting release: {release.tag_name}')
    release.delete_release()
    tag = repo.get_git_ref(f"tags/{release.tag_name}")
    print(f'Deleting tag: {tag.ref}')
    tag.delete()

if __name__ == '__main__':
    for release in repo.get_releases():
        age_days = (datetime.now(timezone.utc) - release.created_at).days
        if age_days > 365:
            purge_release(release)
