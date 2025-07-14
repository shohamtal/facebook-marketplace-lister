import shutil
import zipfile

import requests as requests
import urllib.request
import os

# MAC_CHIP = 'mac-x64' # for intel
MAC_CHIP = 'mac-arm64' # for apple silicone

VER = "137.0.7151.103" # select most closest version to google-chrome
avialable_ver = None

while not avialable_ver:
    versions = requests.get(
        "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json").json()[
        "versions"]
    avialable_ver = next((ver for ver in versions if ver["version"].startswith(VER)), None)
    VER = VER[:-1]

print(f"Downloading chromedriver version {VER}")
driver_path = "chromedriver.zip"
shutil.rmtree("./chromedriver-" + MAC_CHIP, ignore_errors=True)
download_url = next(x for x in avialable_ver["downloads"]["chromedriver"] if x["platform"] == MAC_CHIP)["url"]
urllib.request.urlretrieve(download_url, driver_path)

print(f"Downloaded chromedriver version {download_url}")
with zipfile.ZipFile(driver_path, 'r') as zip_ref:
    zip_ref.extractall("./")
    if os.path.isfile("./chromedriver"):
        os.remove("./chromedriver")

    shutil.move(f"./chromedriver-{MAC_CHIP}/chromedriver", "./")

    os.chmod('chromedriver', 0o755)
