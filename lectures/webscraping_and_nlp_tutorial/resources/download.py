import os
import platform
import zipfile

import requests
from tqdm import tqdm


def download(url, path):
    print(f'Downloading from {url}.')
    response = requests.get(url, stream=True)
    
    with open(path, "wb") as handle:
        for data in tqdm(response.iter_content(chunk_size=65536)):
            handle.write(data)
    
    assert os.path.exists(path)
    print(f'Downloaded data saved to {path}.')


def get_download_dir():
    download_dir = os.path.expanduser('~')
    download_dir = os.path.join(download_dir, 'Downloads')
    assert os.path.exists(download_dir)
    
    return download_dir
        

def chromedriver_download():
    os_map = {
        'Windows': 'win32',
        'Darwin': 'mac64',
        'Linux': 'linux64'
    }
    current_os = os_map[platform.system()]

    chromium_uri = ('https://chromedriver.storage.googleapis.com'
                    '/2.37/chromedriver_{}.zip'.format(current_os))
    chromium_path = os.path.join(get_download_dir(),
                                 'chromedriver_{}.zip'.format(current_os))
    zippath = os.path.join(get_download_dir(), 'chromedriver')
    if current_os == 'win32':
        zippath += '.exe'

    download(url=chromium_uri, path=chromium_path)
    with zipfile.ZipFile(chromium_path, "r") as z:
        z.extractall(get_download_dir())

    assert os.path.exists(zippath)


def googlew2v_download():
    google_w2v_uri = ('https://s3.amazonaws.com/dl4j-distribution'
                      '/GoogleNews-vectors-negative300.bin.gz')
    google_w2v_path = os.path.join(get_download_dir(), 
                                   'GoogleNews-vectors-negative300.bin.gz')
    download(url=google_w2v_uri, path=google_w2v_path)


if __name__ == '__main__':
    chromedriver_download()
    googlew2v_download()
