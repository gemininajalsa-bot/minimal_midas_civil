import requests

class NX:
    version_check = True    # CHANGE IT TO FALSE TO SKIP VERSION CHECK OF LIBRARY
    user_print = True
    debug_request = False
    debug_requestJSON = False
    debug_response = False
    onlyNode = False
    visualiser = True
    modelIDs = {} # Handles the fast MAX ID
    autoTaperGroup = False
    dispWarning = True
    PRODUCT = 'CIVIL'
    SOLVER = 'FES'
    _MEC_VERSIONS = ['9.7.5']
    _isSyncUnit = False
    save_debug_log = False

    units = {
        "FORCE": "KN",
        "DIST": "M",
        "HEAT": "KJ",
        "TEMPER": "C"
    }



class MAPI_BASEURL:
    baseURL = "https://moa-engineers.midasit.com:443/civil"
    server_loc = "Global"
    
    def __init__(self, baseURL:str = "https://moa-engineers.midasit.com:443/civil"):
        MAPI_BASEURL.baseURL = baseURL
        
    @classmethod
    def get_url(cls):
        return MAPI_BASEURL.baseURL
    

    @staticmethod
    def autoURL():
        base_urls = [
            "https://moa-engineers-in.midasit.com:443/civil",
            "https://moa-engineers-kr.midasit.com:443/civil",
            "https://moa-engineers-gb.midasit.com:443/civil",
            "https://moa-engineers-us.midasit.com:443/civil",
            "https://moa-engineers.midasit.cn:443/civil"
            ]
        serv_locations = ["INDIA","KOREA","EUROPE","USA","CHINA"]
        mapi_key = MAPI_KEY.get_key()
        chk = 0
        for i,base_url in enumerate(base_urls):
            url = base_url + "/config/ver"
            headers = {
                "Content-Type": "application/json",
                "MAPI-Key": mapi_key
            }
            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                MAPI_BASEURL(base_url)
                MAPI_BASEURL.server_loc = serv_locations[i]
                chk=1
                break
            
class MAPI_KEY:
    data = ""
    count = 1
    
    def __init__(self, mapi_key:str):
        MAPI_KEY.data = mapi_key
        
    @classmethod
    def get_key(cls):
        my_key = MAPI_KEY.data
        
        return my_key
#---------------------------------------------------------------------------------------------------------------

#2 midas API link code:
def MidasAPI(method:str='', command:str='', body:dict={})->dict:
    
    base_url = MAPI_BASEURL.baseURL
    mapi_key = MAPI_KEY.get_key()

    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }



    if method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)
    else:
        print(f"Invalid HTTP method entered {method}.")
        return False
    resp = response.json()

    return resp


#--------------------------------------------------------------------

def _getUNIT():
    return MidasAPI('GET','/db/UNIT',{})['UNIT']['1']

def _setUNIT(unitJS):
    js = {
        "Assign" : {
            "1" : unitJS
        }
    }
    MidasAPI('PUT','/db/UNIT',js)

