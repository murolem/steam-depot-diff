import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, TypedDict
from git import Repo
from dotenv import load_dotenv

load_dotenv()

# ===============
# == VARIABLES ==
# ===============

# specify the depots for a previous version.
# this list just takes the command the "copy manifest" button outputs on a depot's page, for example:
# download_depot 799600 799601 2417336363700306381
#
# depots for Cosmoteer can be found here https://steamdb.info/app/799600/depots/
# you can at date to determine which manifest is for what update.
# use version history on the wiki to find the update dates you need: https://cosmoteer.wiki.gg/wiki/Version_History

# important depots:
# - "Cosmoteer Core" for its "bin" folder with the executable:
# - "Cosmoteer x86/x64" for the actual data and locales. Use whatever is your architecture.
#
# below are two examples commented out:
# - first is the "Cosmoteer Core" depot
# - second is "Cosmoteer x86" depot
# these are for "0.26.1g" version.
previous_version_depots: list[str] = [
    # 'download_depot 799600 799603 4627408845394697137',  # core
    'download_depot 799600 799601 1252035611068335302',  # data
]

# specify the depots for a new version.
# see description of "previous_version_depots" for details.
#
# below are two examples commented out:
# - first is the "Cosmoteer Core" depot
# - second is "Cosmoteer x86" depot
# these are for "0.26.2" version.
new_version_depots: list[str] = [
    # 'download_depot 799600 799603 4284354019772974139',  # core
    'download_depot 799600 799601 7220058335861384850',  # data
]

# whether to skip both download and validation of the depots.
# this will only work if you have depots already downloaded - otherwise script will fail.
skip_depot_download_and_validate: bool = False

# ===============
# == SCRIPT ==
# ===============

# figure out variables

depot_downloader_dirname = "depot-downloader"
if not os.path.exists(depot_downloader_dirname):
    raise Exception(
        f"depot downloader directory not found; path: '{depot_downloader_dirname}'. create the directory and place the depot downloader inside."
    )

depot_downloader_app_path_matches = [f for f in os.listdir(depot_downloader_dirname) if f.lower().startswith(("depotdownloader"))]
if len(depot_downloader_app_path_matches) == 0:
    raise Exception(
        f"depot downloader executable not found in dir: '{depot_downloader_dirname}'. download the depot downloader and place it inside the directory."
    )

depot_downloader_app_path = os.path.join(depot_downloader_dirname, depot_downloader_app_path_matches[0])

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

def raise_env_var_is_not_specified_exception(env_var_name) -> None:
    raise Exception((
            f"environment variable '{env_var_name}' not found: if you haven't, create '.env' file in the project's directory, and define following variables:"
            + "\nSTEAM_LOGIN=your_steam_login"
            + "\nSTEAM_PASSWORD=your_steam_password"
    ))


steam_login = os.getenv('STEAM_LOGIN')
if steam_login is None:
    raise_env_var_is_not_specified_exception('STEAM_LOGIN')

steam_password = os.getenv('STEAM_PASSWORD')
if steam_password is None:
    raise_env_var_is_not_specified_exception('STEAM_PASSWORD')


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

        subprocess.call(
            f"{depot_downloader_app_path} -username {steam_login} -password {steam_password} -remember-password -validate -dir {depot['rel_output_path']} -app {depot['app_id']} -depot {depot['depot']} -manifest {depot['manifest']}"
        )


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
repo.index.commit("previous ver")

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
repo.index.commit("previous ver")