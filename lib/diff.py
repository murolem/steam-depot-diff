import os.path
import shutil
from git import Repo


def diff(diff_dirpath: str, base_dirpath: str, top_dirpath: str, commit_diff: bool):
    print("Diffing:")
    print("Base: " + base_dirpath)
    print(" Top: " + top_dirpath)
    print("  In: " + diff_dirpath)

    if not os.path.isdir(base_dirpath):
        raise Exception("base dirpath doesn't exist or is not a directory: " + base_dirpath)
    elif not os.path.isdir(top_dirpath):
        raise Exception("top dirpath doesn't exist or is not a directory: " + top_dirpath)

    if os.path.exists(diff_dirpath):
        if not os.path.isdir(diff_dirpath):
            raise Exception("diff dirpath is not a directory: " + diff_dirpath)

        print('Clearing diff directory')
        # error handler specifically for removing git files with questionable perms
        shutil.rmtree(diff_dirpath, onerror=shutil_onerror_fix_perms_and_retry)
    else:
        os.mkdir(diff_dirpath)

    repo = Repo.init(diff_dirpath)

    print("Importing base")
    shutil.copytree(base_dirpath, diff_dirpath, dirs_exist_ok = True)

    print("Staging... (this may take a while)")
    repo.git.add(all=True)

    print("Commiting...")
    repo.index.commit("base")

    print("Preparing for top import")
    for item in [f for f in os.listdir(diff_dirpath) if f != '.git']:
        item_path = os.path.join(diff_dirpath, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        else:
            shutil.rmtree(item_path, onerror=shutil_onerror_fix_perms_and_retry)

    print("Importing top")
    shutil.copytree(top_dirpath, diff_dirpath, dirs_exist_ok = True)

    if commit_diff:
        print("Staging... (this may take a while)")
        repo.git.add(all=True)

        print("Commiting...")
        repo.index.commit("top")


def shutil_onerror_fix_perms_and_retry(func, path, exc_info):
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