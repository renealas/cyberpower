from hashlib import sha256
from operator import mod
from pyexpat import model
from turtle import title
from bs4 import BeautifulSoup
from typing import Optional, List
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json, config
import datetime
import requests
from datetime import datetime
import re

from vdataclass import Firmware

MANIFEST_URL = 'https://www.cyberpowersystems.com/products/software/firmware/'


@dataclass_json
@dataclass
class VendorMetadata:
    product_family: str
    model: str
    os: str
    landing_urls: Optional[List[str]] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    firmware_urls: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    bootloader_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    release_notes_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    md5_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    data: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def main():
    # Printing the List[Firmware] of the function output_firmware.
    manifest = get_manifest(MANIFEST_URL)
    output_firmware(manifest)


def output_firmware(manifest_url: str) -> List[Firmware]:
    vendor_firmwares = []

    firmwareInfoData = []
    for m in manifest_url:
        if m.data != None:
            firmwareInfoData.append(m.data)
    
    for info in firmwareInfoData:
        url = info + '#tab-documents'
        headers = {
         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        }
        response = requests.request("GET", url, headers=headers)
        html = response.content
        response.close()
        soup = BeautifulSoup(html, "html.parser")
        documents = soup.find('div', {'id': 'tab-documents'})
        dataInfo = documents.find('div', {'class': 'document'})
        softInfo = documents.find('div', {'class': 'software'})

        
        # Here the Title and Version
        titleInfo = soup.find('div', {'class': 'row'}).text.strip()
        lastSlash = titleInfo.rfind('/')
        totalSize = len(titleInfo)
        titleData = titleInfo[lastSlash + 1:totalSize].strip()

        vPosition = find_nth(titleData, 'v', 1)
        firmwarePosition = find_nth(titleData, 'Firmware', 1)

        #Here the Model and Version
        model = titleData[0:firmwarePosition].strip()
        version = titleData[vPosition + 1:]

        # Here the Firmware SoftwareData
        softwareInfo = softInfo.find('div', {'class': 'knowledge-center-box'})
        linkData = softwareInfo.find('a', {'class': 'blue-download'})  
        sizeData = linkData.text.strip() 
        sizeDataText = sizeData.replace('Download', '').strip()
        sizeNumber = int(re.sub("[^0-9]", "", sizeDataText))

        sizeFormat = sizeDataText[-2:]
        
        if sizeFormat == 'KB':
            size = str(sizeNumber * 1024)
        elif sizeFormat == 'MB':
            size = str(sizeNumber * 1048576)

        url = linkData.get('href')

        urllastSlash = url.rfind('/')

        filename = url[urllastSlash + 1 :]

        #Initializing Variables to None incase there is not the thing we are looking for
        userManual = None
        releaseNote = None

        #Here the User Manual and the Release Note Info
        try:
            literatureInfo = dataInfo.find_all('div', {'class': 'knowledge-center-box'})

            for info in literatureInfo:
                typeInfo = info.find('p', {'class': 'medium'}).text.strip()

                if 'User Manual' == typeInfo:
                    userManual = info.find('a').get('href')
                
                if 'Release Note' == typeInfo:
                    releaseNote = info.find('a').get('href')
        except:
            pass

        c = Firmware(
          version = version, 
          models = [model],
          filename = filename,
          url = url,
          size_bytes = size,
          release_notes = releaseNote,
          user_manual = userManual,
        )

        if c not in vendor_firmwares:
            vendor_firmwares.append(c)
        else:
            pass
               
    return vendor_firmwares


def get_manifest(manifest_url: str) -> List[VendorMetadata]:

    cyberpower_models = []

    # web page with firmware list
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }
    response = requests.request("GET", manifest_url, headers=headers)
    html = response.content
    response.close()
    soup = BeautifulSoup(html, "html.parser")
    productList = soup.find('ul', {'class': 'products'})
    productInfo = productList.find_all('article')

    for product in productInfo:
        anchorTag = product.find('a', {'class': 'featured-product-title'})
        link = anchorTag.get('href')
        titleData = anchorTag.text.strip()
        findExcess = product.find('div', {'class': 'menu_order_hidden'}).text.strip()

        excessPosition = find_nth(titleData, findExcess, 1)

        titleInfo = titleData[0:excessPosition].strip()

        firmwarePosition = find_nth(titleInfo, 'Firmware', 1)

        title = titleInfo[0:firmwarePosition].strip()

        c = VendorMetadata(
          product_family = None,
          model = title,
          os = None,
          data = link 
        )

        cyberpower_models.append(c)

    return cyberpower_models


if __name__ == "__main__":
    main()
