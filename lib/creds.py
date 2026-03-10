import os
from getpass import getpass
from pathlib import Path
from typing import Callable, NamedTuple, Literal
from dotenv import load_dotenv, get_key, set_key, dotenv_values
from lib.confirm import confirm

DOTENV_PATH = ".env"

class SteamCreds(NamedTuple):
    login: str
    password: str

class VarGetResult(NamedTuple):
    value: str | None
    source: Literal["prompted", "read_from_disk", None]

def get_steam_creds():
    load_dotenv(DOTENV_PATH)

    steam_login_res = var('STEAM_LOGIN', lambda: input_str("Steam Login: "))
    if steam_login_res.value in [None, ""]: return None

    steam_pass_res = var('STEAM_PASSWORD', lambda: input_pass("Steam Password: "))
    if steam_pass_res.value in [None, ""]: return None

    if (
        steam_login_res.source == "prompted" or steam_pass_res.source == "prompted"
    ) and confirm(f"Remember credentials? (will be saved into '{DOTENV_PATH}' file)", default=True):
        var('STEAM_LOGIN', lambda: steam_login_res.value, save_to_disk=True)
        var('STEAM_PASSWORD', lambda: steam_pass_res.value, save_to_disk=True)

    return SteamCreds(
        login=steam_login_res.value,
        password=steam_pass_res.value,
    )

def clear_steam_creds_from_disk():
    if os.path.exists(DOTENV_PATH):
        os.remove(DOTENV_PATH)

def var(var_name: str, prompter: Callable[[], str | None], save_to_disk: bool = False) -> VarGetResult:
    value = os.environ.get(var_name)
    if value in [None, ""]:
        value = prompter()
        if value in [None, ""]:
            return VarGetResult(value=None, source=None)

        if save_to_disk:
            ensure_env_file()
            set_key(DOTENV_PATH, var_name, value)

        return VarGetResult(value=value, source="prompted")

    return VarGetResult(value=value, source="read_from_disk")

def ensure_env_file():
    file_path = Path(DOTENV_PATH)
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
