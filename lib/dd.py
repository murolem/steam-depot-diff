import argparse
import io
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from contextlib import redirect_stderr
from datetime import datetime
from pathlib import Path
from tkinter.messagebox import RETRY
from typing import TypedDict, Optional, Any
from result import Ok, Err, Result, is_ok, is_err
import requests
from lib.creds import get_steam_creds
from lib.download import download

class DepotInit(TypedDict):
    app: str
    depot: str
    manifest: str
    branch: str

class ParseDepotStringError(TypedDict):
    reason: str
    error: Optional[Exception | list[Exception]]
    details: Optional[Any]

class DepotDownloader:
    def __init__(self, dd_dirpath: str, depots_dirpath: str):
        self.dd_dirpath = dd_dirpath
        self.depots_dirpath = depots_dirpath
        self.dd_exec_path = None
        self.is_setup = False
        self.depot_downloads_counter = 0

    @staticmethod
    def parse_depot_string(value: str | None) -> Result[DepotInit, ParseDepotStringError]:
        if value is None:
            return Err(ParseDepotStringError(
                reason="String is None"
            ))

        parsed1 = DepotDownloader._try_parse_depot_string_fmted_as_steam_console(value)
        if isinstance(parsed1, dict):
            return Ok(parsed1)

        parsed2 = DepotDownloader._try_parse_depot_string_fmted_as_depot_downloader(value)
        if isinstance(parsed2, dict):
            return Ok(parsed2)

        return Err(ParseDepotStringError(
            reason="Parse error; methods exhausted",
            error=[
                ["method1", parsed1],
                ["method2", parsed2],
            ],
            details={
                "string": value
            }
        ))

    @staticmethod
    def _try_parse_depot_string_fmted_as_steam_console(value: str) -> DepotInit | Exception:
        # all args are positional
        # example: download_depot 329130 329133 1446294067501623196

        parser = argparse.ArgumentParser(exit_on_error=False)
        parser.add_argument("command")
        parser.add_argument("app")
        parser.add_argument("depot")
        parser.add_argument("manifest")
        try:
            parsed = parser.parse_args(value.split())
            return DepotInit(
                app=parsed.app,
                depot=parsed.depot,
                manifest=parsed.manifest,
                branch="public"
            )
        except Exception as e:
            return e

    @staticmethod
    def _try_parse_depot_string_fmted_as_depot_downloader(value: str) -> DepotInit | Exception:
        # args as options but with a shorthand '-'
        # example: -app 329130 -depot 329133 -manifest 1446294067501623196
        # options: -branch some_branch -beta some_branch

        # normalize option dash by replacing it with double dash
        dash_norm_regex = r'(-)([a-zA-Z0-9]+ [a-zA-Z0-9]+)'
        value = re.sub(dash_norm_regex, "--\\2", value)
        print(value)

        parser = argparse.ArgumentParser(exit_on_error=False)
        parser.add_argument("--app", required=True)
        parser.add_argument("--depot", required=True)
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--beta", "--branch", dest="branch", default="public")
        try:
            options, args = parser.parse_known_args(value.split())
            return DepotInit(
                app=options.app,
                depot=options.depot,
                manifest=options.manifest,
                branch=options.branch
            )
        except Exception as e:
            return e

    def get_exec(
            self,
            releases_endpoint: str = "https://api.github.com/repos/SteamRE/DepotDownloader/releases/latest",
            force_download: bool = False
    ) -> None:
        """
        Setups the DepotDownloader.

        If DepotDownloader is not on disk, downloads its latest release that matches the current platform.

        :param save_dirpath: Directory path to save the executable to.
        :param releases_endpoint: Endpoint to fetch the latest release from.
        :param force_download: Redownloads DepotDownloader even if it exists on disk.
        """

        if force_download:
            self._remove()

        # shortcut: do not redownload if already did
        try:
            self.is_setup = True
            self.dd_exec_path = self._get_exec_filepath()
            return
        except:
            self.is_setup = False
            pass

        print(f"Getting latest DepotDownloader")

        # figure out archive name
        preferred_archive_name = self._guess_dd_archive_name()
        print(f"Expected archive name based on hardware: {preferred_archive_name}")

        # get latest release
        try:
            response = requests.get(releases_endpoint)
        except Exception as e:
            print("ERROR: Failed to get releases info on DepotDownloader from endpoint: " + releases_endpoint)
            raise e
        if not response.ok:
            raise Exception(
                f"Failed to get releases info on DepotDownloader from endpoint. Status code {response.status_code}. Endpoint: " + releases_endpoint)

        data = response.json()
        published_at = data.get('published_at')
        if published_at is not None:
            dt_object = datetime.fromisoformat(published_at)
            pretty_format = "%B %d, %Y at %I:%M %p %Z"
            pretty_string = dt_object.strftime(pretty_format)
            print(f"Retrieved latest release metadata; published {pretty_string}")

        # find the archive to download
        download_url = None
        for asset in data.get('assets', []):
            if asset.get('name') == preferred_archive_name:
                download_url = asset.get('browser_download_url')
                if download_url is not None:
                    download_url = download_url
                    break

        if download_url is None:
            available_names = list(map(lambda e: e.get('name'), data.get('assets', [])))
            raise Exception(
                f"Failed to download DepotDownloader: no release matching system hardware was found. \nExpected: {preferred_archive_name} \nAvailable: {available_names}")

        # download archive
        print("Downloading archive: " + download_url)
        archive_filepath = download(download_url, self.dd_dirpath)

        # unpack archive
        print("Unpacking archive")
        with zipfile.ZipFile(archive_filepath, 'r') as zip_ref:
            zip_ref.extractall(self.dd_dirpath)

        # remove archive file
        print("Cleaning up")
        os.remove(archive_filepath)

        self.is_setup = True
        self.dd_exec_path = self._get_exec_filepath()

    def get_depot(self, depot_init: DepotInit, branch_override: Optional[str], dd_args: Optional[str]) -> str:
        """
        Downloads depot with specified manifest.

        :param depot_init: Depot.
        :param branch_override: Branch override. Overrides branch in depot_init..
        :param dd_args: Extra args to pass to the DepotDownloader executable (as-is).
        :return: Path to the downloaded depot.
        :raises Exception: If download failed.
        """

        app = depot_init.get("app")
        depot = depot_init.get("depot")
        manifest = depot_init.get("manifest")
        branch = branch_override or depot_init.get("branch")

        self.depot_downloads_counter += 1

        print(f"Downloading depot #{self.depot_downloads_counter} | app {app} depot {depot} manifest {manifest}")
        self._assert_setup()

        output_dirpath = os.path.join(self.depots_dirpath, f"app-{app}", f"depot-{depot}", f"manifest-{manifest}")

        creds = get_steam_creds()
        command = f"{self.dd_exec_path} -username {creds.login} -password {creds.password} -remember-password -app {app} -depot {depot} -manifest {manifest} -branch {branch} -validate -dir {output_dirpath}"
        if dd_args:
            command += f" {dd_args}"

        print("Command: " + command.replace(creds.password, "********"))
        try:
            # process_res = subprocess.run(command, shell=True)
            proc = subprocess.run(command, shell=True)
        except Exception as e:
            print("ERROR: depot download failed")
            raise e

        if proc.returncode:
            raise Exception("depot download failed (see above)")

        return output_dirpath

    def _assert_setup(self):
        if not self.is_setup:
            raise Exception("Setup DepotDownloader first by calling setup()")

    def _guess_dd_archive_name(self) -> str:
        """
        Produces the filename of would-be DepotDownloader archive to download that matches the
        current system's OS and architecture. Does no checks to see if the archive actually exists.

        Note: Code partially AI-slopped.

        Returns:
          str: The archive filename (e.g., 'DepotDownloader-linux-x64.zip').

        Raises:
          RuntimeError: If the current platform or architecture is not
                        supported by the available archives.
        """
        # Map sys.platform values to the OS part of the filename
        os_map = {
            'win32': 'windows',
            'linux': 'linux',
            'darwin': 'macos'
        }

        # Map common machine type strings to the architecture suffix
        arch_map = {
            'x86_64': 'x64',
            'AMD64': 'x64',
            'aarch64': 'arm64',
            'arm64': 'arm64'
        }

        # Get the platform key
        platform_key = sys.platform
        os_name = os_map.get(platform_key)
        if os_name is None:
            raise RuntimeError(f"Unsupported operating system: {platform_key}")

        # Get the machine architecture
        machine = platform.machine()
        arch = arch_map.get(machine)
        if arch is None:
            raise RuntimeError(f"Unsupported architecture: {machine}")

        # Build the archive filename
        archive_name = f"DepotDownloader-{os_name}-{arch}.zip"
        return archive_name

    def _get_exec_filepath(self) -> str:
        """Returns the name of the executable DepotDownloader file from its directory.

        :raises Exception: If file not found.
        """

        archive_dirpath_path_obj = Path(self.dd_dirpath)
        if archive_dirpath_path_obj.is_dir():
            for item in archive_dirpath_path_obj.iterdir():
                if item.name.startswith("DepotDownloader"):
                    return os.path.join(archive_dirpath_path_obj, item.name)

        raise Exception("archive executable not found in directory: " + self.dd_dirpath)

    def _remove(self) -> None:
        """Removes DepotDownloader directory from disk if it exists."""

        print("Clearing DepotDownloader directory: " + self.dd_dirpath)
        if os.path.exists(self.dd_dirpath):
            shutil.rmtree(self.dd_dirpath)
