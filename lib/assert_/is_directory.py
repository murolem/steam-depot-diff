from typing import Optional
import os

def assert_is_directory(
        path: str, 
        err_msg: Optional[str]
    ) -> None:
    err_msg = "path is directory assertion failed: path doesn't exist or is not a directory: " + path if err_msg is None else err_msg

    if not os.path.isdir(path):
        raise Exception(err_msg)
