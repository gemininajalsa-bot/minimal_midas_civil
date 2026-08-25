from .._mapi import MidasAPI

def test_call():
    resp = MidasAPI("GET","/db/Node")
    return resp