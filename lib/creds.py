import os
from getpass import getpass
from pathlib import Path
from typing import Callable, NamedTuple, Literal
from dotenv import load_dotenv, get_key, set_key, dotenv_values
from lib.confirm import confirm

class SteamCreds(NamedTuple):
    login: str
    password: str

creds: SteamCreds | None = None
creds_fp: str | None = None

class VarGetResult(NamedTuple):
    value: str | None
    source: Literal["prompted", "read_from_disk", None]

def get_steam_creds(creds_filepath: str) -> SteamCreds:
    """Prompts user for Steam credentials or loads them from disk if they were saved earlier.

    If called before and credentials were produced successfully, returns them instead.
    """

    global creds_fp
    global creds

    creds_fp = creds_filepath
    # quickpath: return creds if already loaded
    if creds:
        return creds

    load_dotenv(creds_filepath)

    steam_login_res = var('STEAM_LOGIN', lambda: input_str("Steam Login: "))
    if steam_login_res.value in [None, ""]: return None

    steam_pass_res = var('STEAM_PASSWORD', lambda: input_pass("Steam Password: "))
    if steam_pass_res.value in [None, ""]: return None

    if (
        steam_login_res.source == "prompted" or steam_pass_res.source == "prompted"
    ) and confirm(f"Remember credentials? (will be saved into '{creds_fp}' file)", default=True):
        var('STEAM_LOGIN', lambda: steam_login_res.value, save_to_disk=True)
        var('STEAM_PASSWORD', lambda: steam_pass_res.value, save_to_disk=True)

    creds = SteamCreds(
        login=steam_login_res.value,
        password=steam_pass_res.value,
    )
    return creds

def clear_steam_creds_from_disk():
    if creds_fp and os.path.exists(creds_fp):
        os.remove(creds_fp)

def var(var_name: str, prompter: Callable[[], str | None], save_to_disk: bool = False) -> VarGetResult:
    if not creds_fp:
        return VarGetResult(value=None, source=None)

    value = os.environ.get(var_name)
    if value in [None, ""]:
        value = prompter()
        if value in [None, ""]:
            return VarGetResult(value=None, source=None)

        if save_to_disk:
            ensure_env_file()
            set_key(creds_fp, var_name, value)

        return VarGetResult(value=value, source="prompted")

    return VarGetResult(value=value, source="read_from_disk")

def ensure_env_file():
    if not creds_fp:
        raise Exception("global Steam credits filepath not set.")

    file_path = Path(creds_fp)
    file_path.touch(exist_ok=True)


def input_str(msg):
    try:
        return input(msg)
    except EOFError:
        return None

def input_pass(msg = "Password: "):
    try:
        return getpass(msg)
    except:
        return None
