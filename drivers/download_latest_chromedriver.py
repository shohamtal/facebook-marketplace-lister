import shutil
import zipfile

import requests as requests
import urllib.request
import os

# VER = "124.0.6367.15" # select most closest version to google-chrome
VER = "126.0.6478.56" # select most closest version to google-chrome
avialable_ver = None

while not avialable_ver:
    versions = requests.get(
        "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json").json()[
        "versions"]
    avialable_ver = next((ver for ver in versions if ver["version"].startswith(VER)), None)
    VER = VER[:-1]

driver_path = "chromedriver.zip"
shutil.rmtree("./chromedriver-mac-x64")
download_url = next(x for x in avialable_ver["downloads"]["chromedriver"] if x["platform"] == 'mac-x64')["url"]
urllib.request.urlretrieve(download_url, driver_path)
with zipfile.ZipFile(driver_path, 'r') as zip_ref:
    zip_ref.extractall("./")
    if os.path.isfile("./chromedriver"):
        os.remove("./chromedriver")

    shutil.move("./chromedriver-mac-x64/chromedriver", "./")

    os.chmod('chromedriver', 0o755)
