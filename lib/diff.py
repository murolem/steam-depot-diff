import os.path
import shutil
from git import Repo
from lib.assert_.is_directory import assert_is_directory


def diff(
    diff_dirpath: str, 
    base_dirpath: str, 
    top_dirpath: str, 
    commit_diff: bool,
    cache_diff_bases: bool
):
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

    print("Processing base")
    base_has_diff_base = has_diff_base(base_dirpath)
    base_has_valid_diff_base = False
    if cache_diff_bases:
        # if has a diff base = use it
        if base_has_diff_base:
            base_repo = Repo(base_dirpath)
            if not base_repo.is_dirty(untracked_files=True):
                # clean, can be used as cache
                print("Found cached base diff")
                base_has_valid_diff_base = True
        # otherwise create the diff base for this depot (manifest)
        else:
            print("Creating base diff cache")
            base_repo = Repo.init(base_dirpath)

            print("Staging (inside base depot)... (this may take a while)")
            base_repo.git.add(all=True)

            print("Committing (inside base depot)...")
            base_repo.index.commit("base")

            base_has_valid_diff_base = True

    print("Importing base")
    shutil.copytree(base_dirpath, diff_dirpath, dirs_exist_ok = True)

    if cache_diff_bases and base_has_valid_diff_base:
        print("Using cached base diff")
    else:
        print("Staging diff... (this may take a while)")
        repo.git.add(all=True)

        print("Committing diff...")
        repo.index.commit("base")

    print("Preparing for top import")
    for item in [f for f in os.listdir(diff_dirpath) if f != '.git']:
        item_path = os.path.join(diff_dirpath, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        else:
            shutil.rmtree(item_path, onerror=shutil_onerror_fix_perms_and_retry)

    print("Importing top")
    shutil.copytree(
        top_dirpath, 
        diff_dirpath, 
        dirs_exist_ok = True, 
        # always ignore .git dir since it would override the current git config
        ignore=lambda directory, contents: ['.git'] if directory == top_dirpath else []
    )

    if commit_diff:
        print("Staging diff... (this may take a while)")
        repo.git.add(all=True)

        print("Committing diff...")
        repo.index.commit("top")


def try_clear_cached_diff_base(manifest_dirpath: str) -> None:
    assert_is_directory(manifest_dirpath, "failed to clear cached diff base: path is not a directory or doesn't exist: " + manifest_dirpath)

    git_dirpath = manifest_dirpath + os.path.sep + ".git"
    if os.path.isdir(git_dirpath):
        print("Cached diff base for clear found; clearing at: " + manifest_dirpath)
        shutil.rmtree(git_dirpath, onerror=shutil_onerror_fix_perms_and_retry)

    pass
    

def has_diff_base(manifest_dirpath: str) -> bool:
    assert_is_directory(manifest_dirpath, "failed to check for diff base: path is not a directory or doesn't exist: " + manifest_dirpath)

    git_dirpath = manifest_dirpath + os.path.sep + ".git"
    if not os.path.isdir(git_dirpath):
        return False
    
    return True

def is_repo_clean(repo: Repo) -> bool:
    is_dirty = repo.is_dirty(untracked_files=True)
    return not is_dirty
    

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