import argparse
import io
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from contextlib import redirect_stderr
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import requests

from lib.creds import get_steam_creds
from lib.download import download

class DepotInit(TypedDict):
    app: str
    depot: str
    manifest_from: str
    manifest_to: str

class DepotDownloader:
    def __init__(self, dd_dirpath: str, depots_dirpath: str):
        self.dd_dirpath = dd_dirpath
        self.depots_dirpath = depots_dirpath
        self.dd_exec_path = None
        self.is_setup = False
        self.depot_downloads_counter = 0

    @staticmethod
    def try_parse_depot_string(value: str) -> DepotInit | None:
        parsed = None
        try:
            f = io.StringIO()
            with redirect_stderr(f):
                parsed = (
                    DepotDownloader._try_parse_depot_string_fmted_as_steam_console(value)
                    or DepotDownloader._try_parse_depot_string_fmted_as_depot_downloader(value)
                    or DepotDownloader._try_parse_depot_string_fmted_as_freehand(value)
                )
        except:
            pass

        return parsed

    @staticmethod
    def _try_parse_depot_string_fmted_as_steam_console(value: str) -> DepotInit | None:
        # example: download_depot 329130 329133 1446294067501623196 1446294067501623197

        parser = argparse.ArgumentParser()
        parser.add_argument("command")
        parser.add_argument("app")
        parser.add_argument("depot")
        parser.add_argument("manifest_from")
        parser.add_argument("manifest_to")
        try:
            parsed = parser.parse_args(value.split())
            return DepotInit(
                app=parsed.app,
                depot=parsed.depot,
                manifest_from=parsed.manifest_from,
                manifest_to=parsed.manifest_to,
            )
        except:
            return None

    @staticmethod
    def _try_parse_depot_string_fmted_as_depot_downloader(value: str) -> DepotInit | None:
        # example: -app 329130 -depot 329133 -manifest 1446294067501623196 1446294067501623197

        parser = argparse.ArgumentParser()
        parser.add_argument("-app", required=True)
        parser.add_argument("-depot", required=True)
        parser.add_argument("-manifest-from", required=True)
        parser.add_argument("-manifest-to", required=True)
        try:
            parsed = parser.parse_args(value.split())
            return DepotInit(
                app=parsed.app,
                depot=parsed.depot,
                manifest_from=parsed.manifest_from,
                manifest_to=parsed.manifest_to,
            )
        except:
            return None

    @staticmethod
    def _try_parse_depot_string_fmted_as_freehand(value: str) -> DepotInit | None:
        # example: 329130 329133 1446294067501623196 1446294067501623197

        parser = argparse.ArgumentParser()
        parser.add_argument("app")
        parser.add_argument("depot")
        parser.add_argument("manifest_from")
        parser.add_argument("manifest_to")
        try:
            parsed = parser.parse_args(value.split())
            return DepotInit(
                app=parsed.app,
                depot=parsed.depot,
                manifest_from=parsed.manifest_from,
                manifest_to=parsed.manifest_to,
            )
        except:
            return None

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

    def get_depot(self, app: str, depot: str, manifest: str, dd_args: str = "") -> str:
        """
        Downloads depot with specified manifest.

        :param app: App ID.
        :param depot: Depot ID.
        :param manifest: Manifest ID.
        :param dd_args: Extra args to pass to the DepotDownloader executable (as-is).
        :return: Path to the downloaded depot.
        :raises Exception: If download failed.
        """

        self.depot_downloads_counter += 1

        print(f"Downloading depot #{self.depot_downloads_counter} | app {app} depot {depot} manifest {manifest}")
        self._assert_setup()

        output_dirpath = os.path.join(self.depots_dirpath, f"app-{app}", f"depot-{depot}", f"manifest-{manifest}")

        creds = get_steam_creds()
        command = f"{self.dd_exec_path} -loginid {self.depot_downloads_counter} -username {creds.login} -password {creds.password} -remember-password -app {app} -depot {depot} -manifest {manifest} -validate -dir {output_dirpath}"
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
