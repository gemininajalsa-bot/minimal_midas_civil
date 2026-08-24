import requests
from ._mapi import NX,MidasAPI,MAPI_KEY,MAPI_BASEURL,MAPI_COUNTRY,Midas_help
_version_ = "1.7.1"

print(f"MIDAS CIVIL-NX PYTHON LIBRARY v{_version_}")
    
from ._node import Node,nodeByID,NodeLocalAxis
from ._element import Element