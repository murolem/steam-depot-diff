import os
import requests
from tqdm import tqdm


# Source - https://stackoverflow.com/a/56951135
# Posted by Ivan Vinogradov, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-09, License - CC BY-SA 4.0
def download(url: str, dest_folder: str) -> str:
    """Downloads file from specified URL. Saves it to the specified directory (created if missing).

    :returns: Path to the saved file.
    """

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1]
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        content_len = int(r.headers['Content-length'] or "0")
        pbar = tqdm(total=content_len)
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    pbar.update(len(chunk))
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())

        pbar.close()
    else:  # HTTP status code 4XX/5XX
        raise Exception("Download failed: status code {}\n{}".format(r.status_code, r.text))

    return file_path