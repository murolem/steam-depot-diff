#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, TypedDict
from git import Repo
from dotenv import load_dotenv
from lib.creds import clear_steam_creds_from_disk, get_steam_creds
from tabulate import tabulate
from lib.dd import DepotDownloader, DepotInit
from lib.diff import diff

VERSION = "1.0.0"

class ArgumentFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass

argparser = argparse.ArgumentParser(
                    prog='Steam Depot Differ',
                    description='Downloads app depots and diffs changes between them.',
                    epilog='Source code: https://github.com/murolem/steam-depot-diff',
                    formatter_class=ArgumentFormatter
)
argparser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')

pos_args_depot_str_help_table = group2_help_table = tabulate([
    ["Steam console", """\
download_depot 329130 329133 5541496194205663540 1446294067501623196
               ^app  ^depot  ^manifest from      ^manifest to
    """],
    ["DepotDownloader", """\
-app 329130 -depot 329133 -manifest 5541496194205663540 1446294067501623196
     ^app          ^depot           ^manifest from      ^manifest to                  
"""],
    ["Freehand", """\
329130 329133 5541496194205663540 1446294067501623196
^app   ^depot ^manifest from      ^manifest to
"""]
], headers=["Format", "Example"], tablefmt="grid")

argparser.add_argument('app_or_depot_string', help=f"""\
Application ID or depot string. 

If used as application ID, other positional arguments must be provided. 
Example: 722730

If used as a depot string, a string containing information about the app, depot and manifest must be provided in this singular argument.
This is useful for when copying depot strings straight from SteamDB.
For convenience, the "manifest to" is just slapped at the back.

Examples:
{pos_args_depot_str_help_table}
""")
argparser.add_argument('depot', help="Depot ID: Example: 799601", nargs="?")
argparser.add_argument('manifest_from', help="Manifest ID of manifest to base the diff at. Example: 5090889475431819364", nargs="?")
argparser.add_argument('manifest_to', help="Manifest ID of manifest to diff with. Example: 4892202388027804689", nargs="?")

group_dd = argparser.add_argument_group("DEPOT DOWNLOADER")
group_dd.add_argument('--dd-path', help="DepotDownloader binary directory. Created and downloaded automatically from the official repo if missing.", default=f"3rd-party{os.path.sep}depot-downloader")
group_dd.add_argument('--redownload-dd', help="Deletes existing DepotDownloader binary (if any) and downloads it again.", action="store_true")
group_dd.add_argument('--dd-args', help="Additional args to pass to DepotDownloader for each depot download.")

group_creds = argparser.add_argument_group("CREDENTIALS")
group_creds.add_argument('--relogin', help="Removes any saved Steam credentials. Useful if entered wrong.", action="store_true")

group_depot = argparser.add_argument_group("DEPOTS")
group_depot.add_argument('--depots-path', help="Directory path for storing depots.", default="depots")

group_diff = argparser.add_argument_group("DIFF")
group_diff.add_argument('--diff-path', help="Directory path for diff process. This is where the diff will happen and can be viewed.", default="diff")

args = argparser.parse_args()

# ===============
# == SETUP ==
# ===============

dd = DepotDownloader(args.dd_path, args.depots_path)

# parse depot string
depot_init: DepotInit
if args.depot is None:
    # only single arg provided, assuming depot string
    depot_init = DepotDownloader.try_parse_depot_string(args.app_or_depot_string)
    if depot_init is None:
        argparser.error("Failed to parse depot string. Make sure the correct format is used. Provided string: " + args.app_or_depot_string)
else:
    depot_init = DepotInit(
        app = args.app_or_depot_string,
        depot = args.depot,
        manifest_from = args.manifest_from,
        manifest_to = args.manifest_to,
    )

dd.get_exec(force_download=args.redownload_dd)
print("DepotDownloader executable: " + dd.dd_exec_path)

print("Getting Steam credentials")
if args.relogin:
    clear_steam_creds_from_disk()
steam_creds = get_steam_creds()
print("Will login to DepotDownloader as: " + steam_creds.login)

depot1 = dd.get_depot(depot_init.get('app'), depot_init.get('depot'), depot_init.get('manifest_from'), args.dd_args)
depot2 = dd.get_depot(depot_init.get('app'), depot_init.get('depot'), depot_init.get('manifest_to'), args.dd_args)

diff(args.diff_path, depot1, depot2)

raise Exception('stop')

# ===============
# == SCRIPT ==
# ===============

# depot downloader metadata dir name that the downloader creates.
depot_downloader_metadata_dir = ".DepotDownloader"

def shututil_rmtree_onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``

    Source: https://stackoverflow.com/a/2656405/15076557
    """
    import stat
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

# parse depots

class Depot(TypedDict):
    app_id: str
    depot: str
    manifest: str
    rel_output_path: str


def parse_depot_str(text: Any) -> Depot:
    if type(text) is not str:
        raise Exception(f"expected string for a depot, got {type(text)} for depot: {text}")

    try:
        _, app_id, depot, manifest = text.split(' ')
        return {
            "app_id": app_id,
            "depot": depot,
            "manifest": manifest,
            "rel_output_path": os.path.sep.join(['depots', depot, manifest])
        }
    except Exception as e:
        print(f"failed to parse a depot string; did you follow the format?")
        raise e


previous_version_depots_parsed: list[Depot] = list(map(parse_depot_str, previous_version_depots))
new_version_depots_parsed: list[Depot] = list(map(parse_depot_str, new_version_depots))

if len(previous_version_depots_parsed) == 0 or len(new_version_depots_parsed) == 0:
    raise Exception("one of depots list is empty - please make sure they are both have depots in them.")

# download depots
if skip_depot_download_and_validate:
    # only check that depot dirs exist
    for depot in previous_version_depots_parsed + new_version_depots_parsed:
        depot: Depot = depot  # adds type info

        assert os.path.exists(depot[
                                  "rel_output_path"]), "one of depots doesn't exists - with disabled download and validation, depot dirs are expected to be downloaded previously; failed depot path: " + \
                                                       depot["rel_output_path"]
else:
    depots_to_download_total = len(previous_version_depots_parsed) + len(new_version_depots_parsed)
    for i, depot in enumerate(previous_version_depots_parsed + new_version_depots_parsed):
        depot: Depot = depot  # adds type info

        print(
            f"[{i + 1} of {depots_to_download_total}] downloading depot {depot['depot']} manifest {depot['manifest']}...")



# generate a diff repo
def ensure_dir_exists_and_empty(path: str) -> None:
    if os.path.exists(path):
        print('clearing out the diff repo...')

        shutil.rmtree(path, onerror=shututil_rmtree_onerror)
    else:
        os.mkdir(path)


rel_diff_repo_path = "diff"

ensure_dir_exists_and_empty(rel_diff_repo_path)

#  =========================

# # copy previous ver depots
# for i, depot in enumerate(previous_version_depots_parsed):
#     print(f"[{i + 1} of {len(previous_version_depots_parsed)}] coping previous ver depot {depot['depot']} manifest {depot['manifest']} to the diff repo...")
#
#     shutil.copytree(depot['rel_output_path'], rel_diff_repo_path + os.path.sep + '01 - previous version', dirs_exist_ok=True)
#
# # copy new ver depots
# for i, depot in enumerate(new_version_depots_parsed):
#     print(f"[{i + 1} of {len(previous_version_depots_parsed)}] coping new ver depot {depot['depot']} manifest {depot['manifest']} to the diff repo...")
#
#     shutil.copytree(depot['rel_output_path'], rel_diff_repo_path + os.path.sep + '02 - new version', dirs_exist_ok=True)

# # print("diff is ready to be viewed! created at: \n" + (os.getcwd() + os.path.sep + rel_diff_repo_path))

#  =========================

repo = Repo.init(rel_diff_repo_path)

# copy previous ver depots
for i, depot in enumerate(previous_version_depots_parsed):
    print(f"[{i + 1} of {len(previous_version_depots_parsed)}] coping previous ver depot {depot['depot']} manifest {depot['manifest']} to the diff repo...")

    shutil.copytree(depot['rel_output_path'], rel_diff_repo_path, dirs_exist_ok=True)

# remove depot downloader metadata
shutil.rmtree(rel_diff_repo_path + os.path.sep + depot_downloader_metadata_dir, onerror=shututil_rmtree_onerror)

# stage and commit
print("staging... (this may take a while)")
repo.git.add(all=True)

print("commiting...")
repo.index.commit("previous version")

# remove depots from diff

print("removing previous ver from the diff repo...")
# remove everything except .git dir
diff_dir_contents_except_git = [f for f in os.listdir(rel_diff_repo_path) if f != '.git']
for file_or_dir_name in diff_dir_contents_except_git:
    rel_file_or_dir_path = rel_diff_repo_path + os.path.sep + file_or_dir_name
    if os.path.isfile(rel_file_or_dir_path):
        os.remove(rel_file_or_dir_path)
    else:
        shutil.rmtree(rel_file_or_dir_path, onerror=shututil_rmtree_onerror)

# copy new ver depots
for i, depot in enumerate(new_version_depots_parsed):
    print(f"[{i + 1} of {len(previous_version_depots_parsed)}] coping new ver depot {depot['depot']} manifest {depot['manifest']} to the diff repo...")

    shutil.copytree(depot['rel_output_path'], rel_diff_repo_path, dirs_exist_ok=True)

# remove depot downloader metadata
shutil.rmtree(rel_diff_repo_path + os.path.sep + depot_downloader_metadata_dir, onerror=shututil_rmtree_onerror)

print("diff is ready to be viewed! created at: \n" + (os.getcwd() + os.path.sep + rel_diff_repo_path))

# stage and commit
print("staging... (this may take a while)")
repo.git.add(all=True)

print("commiting...")
repo.index.commit("new version")