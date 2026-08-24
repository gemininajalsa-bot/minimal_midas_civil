import requests
import sys
import time
from tqdm import tqdm
from typing import Literal

# import polars as pl

_httpMethod = Literal["PUT","POST","DELETE","GET"]
_functionMapping = {

'/doc/new' : 'New Project' ,
'/doc/open' : 'Open Project' ,
'/doc/close' : 'Close Project' ,
'/doc/save' : 'Save' ,
'/doc/saveas' : 'Save As' ,
'/doc/stagas' : 'Save Current Stage As' ,
'/doc/import' : 'Import to Json' ,
'/doc/importmxt' : 'Import to mct/mgt' ,
'/doc/export' : 'Export to Json' ,
'/doc/exportmxt' : 'Export to mct/mgt' ,
'/doc/anal' : 'Perform Analysis' ,

'/db/pjcf' : 'Project Information' ,
'/db/unit' : 'Unit System' ,
'/db/styp' : 'Structure Type' ,
'/db/grup' : 'Structure Group' ,
'/db/bngr' : 'Boundary Group' ,
'/db/ldgr' : 'Load Group' ,
'/db/tdgr' : 'Tendon Group' ,

'/db/node' : 'Node' ,
'/db/elem' : 'Element' ,
'/db/skew' : 'Node Local Axis' ,
'/db/mado' : 'Define Domain' ,
'/db/sbdo' : 'Define Sub-Domain' ,
'/db/doel' : 'Domain-Element' ,
'/db/matl' : 'Material Properties' ,
'/db/imfm' : 'Inelastic Material Properties for Fiber Model' ,
'/db/tdmf' : 'Time Dependent Material Properties - User Defined' ,
'/db/tdmt' : 'Time Dependent Material Properties - Creep/Shrinkage' ,
'/db/tdme' : 'Time Dependent Material Properties - Compressive Strength' ,
'/db/edmp' : 'Change Property' ,
'/db/tmat' : 'Time Dependent Material Link' ,
'/db/epmt' : 'Plastic Material' ,
'/db/sect' : 'Section Properties' ,
'/db/thik' : 'Thickness' ,
'/db/tsgr' : 'Tapered Group' ,
'/db/secf' : 'Section Manager - Stiffness' ,
'/db/rpsc' : 'Section Manager - Reinforcements' ,
'/db/strpssm' : 'Section Manager - Stress Points' ,
'/db/pssf' : 'Section Manager - Plate Stiffness Scale Factor' ,
'/db/vbem' : 'Section Manager - Section for Resultant Forces - Virtual Beam' ,
'/db/vsec' : 'Section Manager - Section for Resultant Forces - Virtual Section' ,
'/db/ewsf' : 'Effective Width Scale Factor' ,
'/db/iehc' : 'Inelastic Hinge Control Data' ,
'/db/iehg' : 'Assign Inelastic Hinge Properties' ,
'/db/fimp' : 'Inelastic Material Properties' ,
'/db/fibr' : 'Fiber Division of Section' ,
'/db/grdp' : 'Group Damping' ,
'/db/essf' : 'Element Stiffness Scale Factor' ,

'/db/cons' : 'Supports' ,
'/db/nspr' : 'Point Spring' ,
'/db/gstp' : 'Define General Spring Type' ,
'/db/gspr' : 'Assign General Spring Supports' ,
'/db/ssps' : 'Surface Spring' ,
'/db/elnk' : 'Elastic Link' ,
'/db/rigd' : 'Rigid Link' ,
'/db/nllp' : 'General Link Properties' ,
'/db/nlnk' : 'General Link' ,
'/db/cglp' : 'Change General Link Property' ,
'/db/frls' : 'Beam End Release' ,
'/db/offs' : 'Beam End Offsets' ,
'/db/prls' : 'Plate End Release' ,
'/db/mlfc' : 'Force-Deformation Function' ,
'/db/sdvi' : 'Seismic Device - Viscous Damper/Oil Damper' ,
'/db/sdve' : 'Seismic Device - Viscoelastic Damper' ,
'/db/sdst' : 'Seismic Device - Steel Damper' ,
'/db/sdhy' : 'Seismic Device - Hysteretic Isolator(MSS)' ,
'/db/sdis' : 'Seismic Device - Isolator(MSS)' ,
'/db/mcon' : 'Linear Constraints' ,
'/db/pzef' : 'Panel Zone Effects' ,
'/db/cldr' : 'Define Constraints Label Direction' ,
'/db/drls' : 'Diaphragm Disconnect' ,

'/db/stld' : 'Static Load Cases' ,
'/db/bodf' : 'Self-Weight' ,
'/db/cnld' : 'Nodal Loads' ,
'/db/bmld' : 'Beam Loads' ,
'/db/sdsp' : 'Specified Displacements of Support' ,
'/db/nmas' : 'Nodal Masses' ,
'/db/ltom' : 'Loads to Masses' ,
'/db/nbof' : 'Nodal Body Force' ,
'/db/pslt' : 'Define Pressure Load Type' ,
'/db/pres' : 'Assign Pressure Loads' ,
'/db/pnld' : 'Define Plane Load Type' ,
'/db/pnla' : 'Assign Plane Loads' ,
'/db/fbld' : 'Define Floor Load Type' ,
'/db/fbla' : 'Assign Floor Loads' ,
'/db/fmld' : 'Finishing Material Loads' ,
'/db/posp' : 'Parameter of Soil Properties' ,
'/db/epst' : 'Static Earth Pressure' ,
'/db/epse' : 'Seismic Earth Pressure' ,
'/db/posl' : 'Parameter of Seismic Loads' ,

'/db/etmp' : 'Element Temperature' ,
'/db/gtmp' : 'Temperature Gradient' ,
'/db/btmp' : 'Beam Section Temperature' ,
'/db/stmp' : 'System Temperature' ,
'/db/ntmp' : 'Nodal Temperature' ,

'/db/tdnt' : 'Tendon Property' ,
'/db/tdna' : 'Tendon Profile' ,
'/db/tdcs' : 'Tendon Location for Composite Section' ,
'/db/tdpl' : 'Tendon Prestress' ,
'/db/prst' : 'Prestress Beam Loads' ,
'/db/ptns' : 'Pretension Loads' ,
'/db/exld' : 'External Type Load Case for Pretension' ,
'/db/plcb' : 'Pre-Composite Section' ,

'/db/mvcd' : 'Moving Load Code' ,
'/db/llan' : 'Traffic Line Lanes' ,
'/db/llanch' : 'Traffic Line Lanes - China' ,
'/db/llanid' : 'Traffic Line Lanes - India' ,
'/db/llantr' : 'Traffic Line Lanes - Transverse' ,
'/db/llanop' : 'Traffic Line Lanes - Moving Load Optimizaion' ,
'/db/slan' : 'Traffic Surface Lanes' ,
'/db/slanch' : 'Traffic Surface Lanes - China' ,
'/db/slanop' : 'Traffic Surface Lanes - Moving Load Optimization' ,
'/db/mvhl' : 'Vehicles' ,

'/db/mvhltr' : 'Vehicles - Transverse' ,
'/db/mvld' : 'Moving Load Cases' ,
'/db/mvldch' : 'Moving Load Cases - China' ,
'/db/mvldid' : 'Moving Load Cases - India' ,
'/db/mvldbs' : 'Moving Load Cases - BS' ,
'/db/mvldeu' : 'Moving Load Cases - Eurocode' ,
'/db/mvldpl' : 'Moving Load Cases - Poland' ,
'/db/mvldtr' : 'Moving Load Cases - Transverse' ,
'/db/crgr' : 'Concurrent Reaction Group' ,
'/db/cjfg' : 'Concurrent Joint Force Group' ,
'/db/mvhc' : 'Vehicle Classes' ,
'/db/sinf' : 'Plate Element for Influence Surface' ,
'/db/mlsp' : 'Lane Support - Negative Moments at Interior Piers' ,
'/db/mlsr' : 'Lane Support - Reactions at Interior Piers' ,
'/db/dyla' : 'Dynamic Load Allowance' ,
'/db/impf' : 'Additional Impact Factor' ,
'/db/dyfg' : 'Railway Dynamic Factor' ,
'/db/dynf' : 'Railway Dynamic Factor by Element' ,

'/db/spfc' : 'Response Spectrum Functions - User Type' ,
'/db/splc' : 'Response Spectrum Load Cases' ,
'/db/thgc' : 'Time History Global Control' ,
'/db/this' : 'Time History Load Cases' ,
'/db/thfc' : 'Time History Functions' ,
'/db/thga' : 'Ground Acceleration' ,
'/db/thnl' : 'Dynamic Nodal Loads' ,
'/db/thsl' : 'Time Varying Static Loads' ,
'/db/thms' : 'Multiple Support Excitation' ,

'/db/stag' : 'Define Construction Stage' ,
'/db/cscs' : 'Composite Section for Construction Stage' ,
'/db/tmld' : 'Time Loads for Construction Stage' ,
'/db/stbk' : 'Set-Back Loads for Nonlinear Construction Stage' ,
'/db/cmcs' : 'Camber for Construction Stage' ,
'/db/crpc' : 'Creep Coefficient for Construction Stage' ,

'/db/smpt' : 'Settlement Group' ,
'/db/smlc' : 'Settlement Load Cases' ,

'/db/actl' : 'Main Control Data' ,
'/db/pdel' : 'P-Delta Analysis Control' ,
'/db/buck' : 'Buckling Analysis Control' ,
'/db/eigv' : 'Eigenvalue Analysis Control' ,
'/db/hhct' : 'Heat of Hydration Analysis Control' ,
'/db/mvct' : 'Moving Load Analysis Control' ,
'/db/mvctch' : 'Moving Load Analysis Control - China' ,
'/db/mvctid' : 'Moving Load Analysis Control - India' ,
'/db/mvctbs' : 'Moving Load Analysis Control - BS' ,
'/db/mvcttr' : 'Moving Load Analysis Control - Transverse' ,
'/db/smct' : 'Settlement Analysis Control Data' ,
'/db/nlct' : 'Nonlinear Analysis Control Data' ,
'/db/stct' : 'Construction Stage Analysis Control Data' ,
'/db/bcct' : 'Boundary Change Assignment' ,

'/db/lcom-gen' : 'Load Combinations - General' ,
'/db/lcom-conc' : 'Load Combinations - Concrete Design' ,
'/db/lcom-steel' : 'Load Combinations - Steel Design' ,
'/db/lcom-src' : 'Load Combinations - SRC Design' ,
'/db/lcom-stlcomp' : 'Load Combinations - Composite Steel Girder Design' ,
'/db/lcom-seismic' : 'Load Combinations - Seismic Design' ,
'/db/cutl' : 'Cutting Line' ,
'/db/clwp' : 'Plate Cutting Line Diagram' ,

}


def Midas_help():
    pass


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

    # Function for quick saving of JSON
    @staticmethod
    def saveJSON(jsonData,fileLocation = "jsData.json"):
        import json
        with open(fileLocation, "w", encoding="utf-8") as f:
            json.dump(jsonData, f, indent=4, ensure_ascii=False)
        return True

    # Function to quickly print text in a box , width -> CENTER Align
    @staticmethod
    def box_print(text:str="HELLO WORLD",width:int=None,pad:int=1,text_col="",border_col=""):

        padding = pad

        lines = text.splitlines()

        length = max([len(line) for line in lines])

        if width:
            length = max(length,width)
        leng = length+2*padding


        print("╭","─"*leng,"╮")
        for line in lines:
            if width:
                gap = (leng-len(line))//2
                print("│"," "*gap,line," "*(leng-len(line)-gap),"│",sep="")
            else:
                print("│"," "*padding,line," "*(leng-padding-len(line)),"│",sep="")
        print("╰","─"*leng,"╯".RESET_ALL,sep="")

        return True
    
        

class MAPI_COUNTRY:
    
    country = "US"

    def __init__(self,country:str="US"):
        if country.lower() in ['us','ch','kr','jp']:
            MAPI_COUNTRY.country = country.upper()
        else:
            MAPI_COUNTRY.country = 'US'
        
        MAPI_BASEURL.setURLfromRegistry()
        MAPI_KEY.get_key()  # Intial Key from registry


class MAPI_BASEURL:
    baseURL = "https://moa-engineers.midasit.com:443/civil"
    server_loc = "Global"
    
    def __init__(self, baseURL:str = "https://moa-engineers.midasit.com:443/civil"):
        MAPI_BASEURL.baseURL = baseURL
        
    @classmethod
    def get_url(cls):
        return MAPI_BASEURL.baseURL
    
    @classmethod
    def setURLfromRegistry(cls):
        tqdm.write(" 🌐   BASE URL is not defined. Click on Apps > API Settings to copy the BASE URL Key.Define it using MAPI_BASEURL('https://moa-engineers.midasit.com:443/civil')")
        sys.exit(0)

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
        if chk==0:
            tqdm.write(f" 🌐   Kindly manually enter the BASE URL. Refer to https://moa.midasit.com/services to find the correct URL.")
            sys.exit(0)
            
class MAPI_KEY:
    data = ""
    count = 1
    
    def __init__(self, mapi_key:str):
        MAPI_KEY.data = mapi_key
        
    @classmethod
    def get_key(cls):
        if MAPI_KEY.data == "":
            tqdm.write(f"🔑   MAPI KEY is not defined. Click on Apps > API Settings to copy the MAPI Key. Define it using MAPI_KEY('xxxx')")
            sys.exit(0)
        else:
            my_key = MAPI_KEY.data
        
        return my_key
#---------------------------------------------------------------------------------------------------------------

#2 midas API link code:
def MidasAPI(method:_httpMethod, command:str, body:dict={})->dict:
    
    base_url = MAPI_BASEURL.baseURL
    mapi_key = MAPI_KEY.get_key()

    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }

    if MAPI_KEY.count == 1:
        MAPI_KEY.count =0

        if NX.user_print:
            _checkUSER()

        if NX.save_debug_log:
            sys.stdout = open("midas_civil_debug_log.txt", "w", encoding="utf-8")




    start_time = time.perf_counter()


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

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    if NX.debug_request:
        tqdm.write(f">>   METHOD : {method} |  URL : {command} | STATUS :  {response.status_code} | TIME : {elapsed_time:.4f} sec ")
    if NX.debug_requestJSON:
        tqdm.write(">>  "+str(body))
    if NX.debug_response:
        tqdm.write("<<  "+str(response.json()))

    if MAPI_KEY.count == 0:
        MAPI_KEY.count = -1
        if response.status_code == 404:
            print("╭─ 💀   ─────────────────────────────────────────────────────────────────────────────╮")
            print(f"│  Civil NX model is not connected.  Click on 'Apps > Connect' in Civil NX.          │")
            print(f"│  Make sure the MAPI Key in python code is matching with the MAPI key in Civil NX.  │")
            print("╰────────────────────────────────────────────────────────────────────────────────────╯")
            sys.exit(0)
        elif response.status_code == 401:
            print("╭─ 💀   ─────────────────────────────────────────────────────────────────────────────╮")
            print(f"│  MAPI KEY entered is invalid.                                                      │")
            print(f"│  Please consider refreshing MAPI-Key in CIVIL NX and resending the request.        │")
            print("╰────────────────────────────────────────────────────────────────────────────────────╯")
            sys.exit(0)
    
    resp = response.json()
    if NX.dispWarning:
        if 'error' in resp:
            cmd = _functionMapping.get(command.lower(),command)
            tqdm.write(f'    ⚠️      Error observed in {cmd}.   |   URL : {command}')
            tqdm.write(f'           Error : {resp["error"]["message"]}')        


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


def _checkUSER():
    response =  MidasAPI('GET','/config/ver',{})
    if 'VER' in response:
        resp:dict = response['VER']
        _product = resp['NAME']
        if 'CIVIL' in _product:
            NX.PRODUCT = 'CIVIL'
        elif 'GEN' in _product:
            NX.PRODUCT = 'GEN'
        
        _version = resp.get('VERSION','9.6.0')
        if _version in NX._MEC_VERSIONS:
            NX.SOLVER == 'MEC'
 

        # print(f"{' '*15}Connected to {resp['NAME']}")
        # print(f"{' '*15}USER : {resp['USER']}          COMPANY : {resp['COMPANY']}")

        ln1 = f"Connected to {resp['NAME']}            SERVER : {MAPI_BASEURL.server_loc}"
        ln2 = f"USER : {resp['USER']}          COMPANY : {resp['COMPANY']}"

        lg_ln1 = 66-len(ln1)
        lg_ln2 = 70-len(ln2)

        line1 = f"│{' '*12} {ln1} {' '*lg_ln1} 🟢 │"
        line2 = f"│{' '*12} {ln2} {' '*lg_ln2}│"
        tqdm.write('╭─ 🔔  ──────────────────────────────────────────────────────────────────────────────╮')
        tqdm.write(line1)
        tqdm.write(line2)
        tqdm.write('╰────────────────────────────────────────────────────────────────────────────────────╯')

        if NX.PRODUCT !='CIVIL':
            tqdm.write('╭─ ⚠️   ──────────────────────────────────────────────────────────────────────────────╮')
            tqdm.write(f"│      Warning: You are using midas_civil library to connect with GEN NX.            │")
            tqdm.write(f"│      Some GEN NX specific options may not be avaialble.                            │")
            tqdm.write('╰────────────────────────────────────────────────────────────────────────────────────╯')


        # print('─'*86)