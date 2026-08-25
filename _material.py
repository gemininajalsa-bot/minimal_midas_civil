from ._mapi import MidasAPI
from typing import Literal

_dbConc = Literal["KSCE-LSD15(RC)","KS01-Civil(RC)","KS-Civil(RC)","KS19(RC)","KS01(RC)","KS(RC)","ASTM19(RC)","ASTM(RC)","U.S.C(US)(RC)","U.S.C(SI)(RC)","NMX NTC-2017(RC)","CSA(RC)","JIS(RC)","JIS-Civil(RC)","JTJ023-85(RC)","Q/CR 9300-18(RC)","GB 50917-13(RC)","GB10(RC)","GB(RC)","GB-Civil(RC)","TB10092-17(RC)","JTG3362-18(RC)","JTG04(RC)","TB05(RC)","BS(RC)","EN04(RC)","EN(RC)","NTC08(RC)","NTC12(RC)","NTC18(RC)","UNI(RC)","SS(RC)","GOST-SP(RC)","GOST-SNIP(RC)","IRC(RC)","IRS(RC)","IS(RC)","CNS560-18(RC)","CNS560(RC)","CNS(RC)","AS17(RC)","TMH7(RC)","PNS49(RC)","SNI(RC)","TIS(RC)","TIS(MKS)(RC)"]
_CreepIRCCementType =Literal['SL','NR','RS']
_CreepIRCAggType =Literal['Basalt','Quartzite','Limestone','Sandstone']
_map_CreepIRCAggTypeIndex = {'Basalt':0,'Quartzite':1,'Limestone':2,'Sandstone':3}
_CreepIRCYear = Literal['2011','2000','2020']
_CreepCEBFIPYear = Literal['2010','1990','1978']
_CreepCEBFIPCementType =Literal['SL','NR','RS']
_CReepACICuring = Literal['MOIST','STEAM']
_CreepACIMatType = Literal['CODE','USER']
_CreepEuropeanCementType = Literal['Class S','Class N','Class R']
_CreepASNZStandard = Literal['AS_5100_5_2017','AS_5100_5_2016','AS_RTA_5100_5_2011','AS_3600_2009','NEWZEALAND']
_CreepChineseStandard = Literal['CHINESE','JTG','CHINA_JTG3362_2018']
_CreepChineseHumidityType = Literal['CU','RH']
_CreepKoreanStandard = Literal['KDS_2016','KSI_USD12','KSCE_2010','KS']
_CreepKoreanCementType = Literal['SL','NR','RS'] 
_CreepJapanStandard = Literal['JSCE_12','JSCE_07','JSCE']
_CreepJapaneseCalMethod = Literal['JSCE','AIJ']
_CreepJapaneseHumidityType = Literal['RH','CU'] 
_CreepJapaneseCementType = Literal['RH','NC']
_CompStrengthIRCYear = Literal['2000','2011','2020']
_CompStrengthCEBFIPYear = Literal['1978','1990','2010']
_CompStrengthASStandard = Literal['AS5100.5-2017','AS5100.5-2016','AS/RTA5100.5-2011','AS3600-2009']

class Material:
    mats:list['Material'] = []
    ids = []
    _dic = {}
    def __init__(self,data,id=None):
        if id == None: id =0
        if Material.ids == []:
            count = 1
        else:
            count = max(Material.ids)+1
        if id == 0 or id in Material.ids: self.ID = count
        if id!= 0 and id not in Material.ids: self.ID = id

        self.DATA = data
        self.NAME = data["NAME"]
        self.TYPE = data["TYPE"]

        Material.mats.append(self)
        Material.ids.append(self.ID)
        Material._dic[data["NAME"]] = self.ID
    
    @classmethod
    def json(cls):
        json = {"Assign":{}}
        for k in cls.mats:
            json["Assign"][k.ID]=k.DATA
        return json

    @staticmethod
    def create_only():
        return MidasAPI("PUT","/db/MATL",Material.json())

    @staticmethod
    def get():
        return MidasAPI("GET","/db/MATL")


    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/MATL")
        Material.clear()

    @staticmethod
    def clear():
        Material.mats=[]
        Material.ids=[]

    @staticmethod
    def sync(bMaterialParam=False):
        Material.clear()
        a = Material.get()
        if a != {'message': ''}:
            if list(a['MATL'].keys()) != []:
                for j in a['MATL'].keys():
                    Material(a['MATL'][j], int(j))
        if bMaterialParam:
            jsMat = {
                "Argument": {
                    "TABLE_NAME": "SS_Mat_Prop",
                    "TABLE_TYPE": "MATERIAL"
                }
            }

            sectPropJS = MidasAPI('POST',"/post/TABLE",jsMat)["SS_Mat_Prop"]["DATA"]

            for mat in sectPropJS:
                _id = int(mat[1])

                _matObj = Material.mats[Material.ids.index(_id)]
                _matObj.E = float(mat[8])
                _matObj.V = float(mat[9])
                _matObj.ALPHA = float(mat[10])
                _matObj.W = float(mat[11])
                _matObj.D = float(_matObj.DATA["DAMP_RAT"])

        # ----------------------------------  ALL FUNCTIONS  ---------------------------------------------------
    
    @staticmethod
    def create():
        if Material.mats!=[] : Material.create_only()
        if CreepShrinkage.mats!=[] : CreepShrinkage.create()
        if CompStrength.mats!=[] : CompStrength.create()
        if TDMatLink.json()!={'Assign':{}} : TDMatLink.create()
        if ChangeProperty.data: ChangeProperty.create()
        
    
    @staticmethod
    def deleteAll():
        Material.delete()
        CreepShrinkage.delete()
        CompStrength.delete()
        ChangeProperty.delete()

    @staticmethod
    def clearAll():
        Material.clear()
        CreepShrinkage.clear()
        CompStrength.clear()
        ChangeProperty.clear()
        


# ---------------------------------  CONCRETE MATERIAL --------------------------------------------------------------

    class CONC:


        # ----------------------------------  DB MATERIAL ---------------------------------------------------

        def __init__(self,name='',standard:_dbConc='',db='',spec_heat:float=0,heat_conduct:float=0,id:int=None,):
            if id == None: id =0  
            js =  {
                "TYPE": "CONC",
                "NAME": name,
                "DAMP_RAT": 0.05,
                "HE_SPEC": spec_heat,
                "HE_COND": heat_conduct,
                "PARAM": [
                    {
                        "P_TYPE": 1,
                        "STANDARD": standard,
                        "CODE": "",
                        "DB": db,
                    }
                ]
            }
            temp = Material(js,id)
            self.ID = temp.ID
            self.DATA = js


        # ----------------------------------  USER MATERIAL ---------------------------------------------------

        class User:
            def __init__(self,name='',E=0,pois=0,den=0,mass=0,therm=0,spec_heat:float=0,heat_conduct:float=0,id:int=None,):
                if id == None: id =0
                js =  {
                    "TYPE": "CONC",
                    "NAME": name,
                    "DAMP_RAT": 0.05,
                    "HE_SPEC": spec_heat,
                    "HE_COND": heat_conduct,
                    "PARAM": [
                        {
                            "P_TYPE": 2,
                            "ELAST": E,
                            "POISN": pois,
                            "THERMAL": therm,
                            "DEN": den,
                            "MASS": mass
                        }
                    ]
                }
                temp = Material(js,id)
                self.ID = temp.ID
                self.DATA = js

    

# ---------------------------------  STEEL MATERIAL --------------------------------------------------------------

    class STEEL:

        # ----------------------------------  DB MATERIAL ---------------------------------------------------

        def __init__(self,name='',standard='',db='',spec_heat:float=0,heat_conduct:float=0,id:int=None,):
            if id == None: id =0
            js =  {
                "TYPE": "STEEL",
                "NAME": name,
                "DAMP_RAT": 0.05,
                "HE_SPEC": spec_heat,
                "HE_COND": heat_conduct,
                "PARAM": [
                    {
                        "P_TYPE": 1,
                        "STANDARD": standard,
                        "CODE": "",
                        "DB": db,
                    }
                ]
            }
            temp = Material(js,id)
            self.ID = temp.ID
            self.DATA = js


        # ----------------------------------  USER MATERIAL ---------------------------------------------------

        class User:
            def __init__(self,name='',E=0,pois=0,den=0,mass=0,therm=0,spec_heat:float=0,heat_conduct:float=0,id:int=None,):
                if id == None: id =0
                js =  {
                    "TYPE": "STEEL",
                    "NAME": name,
                    "DAMP_RAT": 0.05,
                    "HE_SPEC": spec_heat,
                    "HE_COND": heat_conduct,
                    "PARAM": [
                        {
                            "P_TYPE": 2,
                            "ELAST": E,
                            "POISN": pois,
                            "THERMAL": therm,
                            "DEN": den,
                            "MASS": mass
                        }
                    ]
                }
                temp = Material(js,id)
                self.ID = temp.ID
                self.DATA = js




# ---------------------------------  USER MATERIAL --------------------------------------------------------------

    class USER:

        def __init__(self,name:str='',E:float=0,pois:float=0,den:float=0,mass:float=0,therm:float=0,spec_heat:float=0,heat_conduct:float=0,id:int=None,):
            if id == None: id =0
            js =  {
                "TYPE": "USER",
                "NAME": name,
                "DAMP_RAT": 0.05,
                "HE_SPEC": spec_heat,
                "HE_COND": heat_conduct,
                "PARAM": [
                    {
                        "P_TYPE": 2,
                        "ELAST": E,
                        "POISN": pois,
                        "THERMAL": therm,
                        "DEN": den,
                        "MASS": mass
                    }
                ]
            }
            temp = Material(js,id)
            self.ID = temp.ID
            self.DATA = js


# ------------------------------------------ TIME DEPENDENT - CREEP and SHRINKAGE ----------------------------------------------------

class CreepShrinkage:
    mats:list['CreepShrinkage'] = []
    ids = []
    def __init__(self,data,id:int=None):
        if id == None: id =0
        if CreepShrinkage.ids == []:
            count = 1
        else:
            count = max(CreepShrinkage.ids)+1
        if id == 0 or id in CreepShrinkage.ids: self.ID = count
        if id!= 0 and id not in CreepShrinkage.ids: self.ID = id

        self.DATA = data

        CreepShrinkage.mats.append(self)
        CreepShrinkage.ids.append(self.ID)

    @classmethod
    def json(cls):
        json = {"Assign":{}}
        for k in cls.mats:
            json["Assign"][k.ID]=k.DATA
        return json

    @staticmethod
    def create():
        MidasAPI("PUT","/db/TDMT",CreepShrinkage.json())

    @staticmethod
    def get():
        return MidasAPI("GET","/db/TDMT")


    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/TDMT")
        CreepShrinkage.clear()

    @staticmethod
    def clear():
        CreepShrinkage.mats=[]
        CreepShrinkage.ids=[]

    @staticmethod
    def sync():
        a = CreepShrinkage.get()
        if a != {'message': ''}:
            if list(a['TDMT'].keys()) != []:
                CreepShrinkage.mats = []
                CreepShrinkage.ids=[]
                for j in a['TDMT'].keys():
                    CreepShrinkage(a['TDMT'][j], int(j))

    # ---------------------------------  IRC CnS --------------------------------------------------------------

    class IRC:
        def __init__(self,name: str, code_year: _CreepIRCYear = 2011, fck: float = 0, notional_size: float = 1,
                     relative_humidity: float = 70, age_shrinkage: int = 3, type_cement: _CreepIRCCementType = 'NR', type_aggregate:_CreepIRCAggType='Basalt',id: int = None):

            if id == None: id =0

            if type_cement == "SL":
                type_cement = "RS"
            elif type_cement == "RS":
                type_cement = "SL"

            js =  {
                "NAME": name,
                "CODE": "INDIA_IRC_18_2000",
                "STR": fck,
                "HU": relative_humidity,
                "AGE": age_shrinkage,
                "MSIZE": notional_size
            }

            if code_year == 2020 or int(code_year) == 2020:
                js["CODE"] = "INDIA_IRC_112_2020"
                js["CTYPE"] = type_cement
                js["TYPEOFAFFR"] = _map_CreepIRCAggTypeIndex.get(type_aggregate,0)
            elif code_year == 2011 or int(code_year) == 2011:
                js["CODE"] = "INDIA_IRC_112_2011"
                js["CTYPE"] = type_cement
            else:
                js["CODE"] = "INDIA_IRC_18_2000"
            
            

            temp = CreepShrinkage(js,id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  CEB-FIP CnS --------------------------------------------------------------

    class CEB_FIP:
        def __init__(self, name: str, code_year: _CreepCEBFIPYear = 2010, fck: float = 0, notional_size: float = 1,
                     relative_humidity: float = 70, age_shrinkage: int = 3, type_cement: _CreepCEBFIPCementType = 'RS',
                     type_of_aggregate: int = 0, id: int = None):

            if id == None: id =0
            code_name = ""
            if code_year == 2010 or int(code_year) == 2010:
                code_name = "CEB_FIP_2010"
            elif code_year == 1990 or int(code_year) == 1990:
                code_name = "CEB"
            elif code_year == 1978 or int(code_year) == 1978:
                code_name = "CEB_FIP_1978"
            else:
                code_name = "CEB_FIP_2010"

            js = {
                "NAME": name,
                "CODE": code_name,
                "STR": fck,
                "HU": relative_humidity,
                "AGE": age_shrinkage,
                "MSIZE": notional_size,
                "CTYPE": type_cement,
            }
            if code_year == 2010 or int(code_year) == 2010:
                js["TYPEOFAFFR"] = type_of_aggregate

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  ACI CnS --------------------------------------------------------------

    class ACI:
        def __init__(self, name: str, fck: float = 0, relative_humidity: float = 70, age_shrinkage: int = 3,
                     vol_surface_ratio: float = 1.2, cfact_a: float = 4, cfact_b: float = 0.85,
                     curing_method: _CReepACICuring = "MOIST", material_type: _CreepACIMatType = "CODE", cement_content: float = 24,
                     slump: float = 1.1, fine_agg_percent: float = 12, air_content: float = 13,
                     creep_coeff: float = None, shrink_strain: float = None, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "ACI",
                "STR": fck,
                "HU": relative_humidity,
                "AGE": age_shrinkage,
                "VOL": vol_surface_ratio,
                "CFACTA": cfact_a,
                "CFACTB": cfact_b,
                "TYPE": material_type,
                "CMETHOD": curing_method
            }

            if material_type == "CODE":
                js.update({
                    "CEMCONTENT": cement_content,
                    "SLUMP": slump,
                    "FAPERCENT": fine_agg_percent,
                    "AIRCONTENT": air_content
                })
            elif material_type == "USER":
                js.update({
                    "CREEPCOEFF": creep_coeff if creep_coeff is not None else 1.4,
                    "SHRINKSTRAIN": shrink_strain if shrink_strain is not None else 500
                })

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  AASHTO CnS --------------------------------------------------------------

    class AASHTO:
        def __init__(self, name: str, fck: float = 0, relative_humidity: float = 70, age_shrinkage: int = 3,
                     vol_surface_ratio: float = 1.2, b_expose: bool = False, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "AASHTO",
                "STR": fck,
                "HU": relative_humidity,
                "AGE": age_shrinkage,
                "VOL": vol_surface_ratio,
                "bEXPOSE": b_expose
            }
            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  European CnS --------------------------------------------------------------

    class European:
        def __init__(self, name: str, fck: float = 0, relative_humidity: float = 70, age_shrinkage: int = 3,
                     notional_size: float = 1.2, type_cement: _CreepEuropeanCementType = "Class N", t_code: int = 0, b_silica: bool = False, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "EUROPEAN",
                "STR": fck,
                "HU": relative_humidity,
                "AGE": age_shrinkage,
                "MSIZE": notional_size,
                "CTYPE": type_cement,
                "TCODE": t_code,
            }
            if t_code == 1:
                js["bSILICA"] = b_silica

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  Russian CnS --------------------------------------------------------------
    class Russian:
        def __init__(self, name: str, fck: float, relative_humidity: float, module_exposed_surface: float,
                     age_concrete: int, water_content: float, max_aggregate_size: float, air_content: float,
                     specific_cement_paste_content: float, curing_method: int = 0,cement_type=1, fast_accumulating_creep: bool = False,
                     concrete_type: int = 0, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "RUSSIAN",
                "STR": fck,
                "HU": relative_humidity,
                "M": module_exposed_surface,
                "AGE": age_concrete,
                "CMETH": curing_method,
                "iCTYPE": cement_type,
                "CREEP": fast_accumulating_creep,
                "CONCT": concrete_type,
                "W": water_content,
                "MAXS": max_aggregate_size,
                "A": air_content,
                "PZ": specific_cement_paste_content
            }
            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  AS & NZ CnS -------------------------------------------------
    class AS_NZ:
        def __init__(self, name: str, standard: _CreepASNZStandard, fck: float, concrete_age: int,
                    hypothetical_thickness: float, drying_shrinkage_type: int = 0,
                    user_defined_shrinkage_strain: float = 0, humidity_factor: float = 0.72,
                    exposure_environment: int = 0, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": standard,
                "STR": fck,
                "THIK": hypothetical_thickness,
                "AGE": concrete_age,
                "iEPS_DRY": drying_shrinkage_type,
            }

            # Internal maps for predefined shrinkage values from the manual
            as_strain_map = {0: 800.0, 1: 900.0, 2: 1000.0}
            nz_strain_map = {0: 1500.0, 1: 1460.0, 2: 1315.0, 3: 1080.0, 4: 1000.0, 5: 990.0, 6: 950.0, 7: 775.0, 8: 735.0, 9: 570.0}

            eps_dry_value = None
            is_as_code = standard != "NEWZEALAND"
            is_nz_code = standard == "NEWZEALAND"

            # Check for user-defined cases first
            if is_as_code and drying_shrinkage_type == 3:
                eps_dry_value = user_defined_shrinkage_strain
            elif is_nz_code and drying_shrinkage_type == 10:
                eps_dry_value = user_defined_shrinkage_strain
            # Otherwise, look up the predefined value from the appropriate map
            elif is_as_code:
                eps_dry_value = as_strain_map.get(drying_shrinkage_type)
            elif is_nz_code:
                eps_dry_value = nz_strain_map.get(drying_shrinkage_type)

            js["EPS_DRY"] = eps_dry_value

            # Add parameters specific to the standard
            if is_nz_code:
                js["FS"] = humidity_factor
            else: # Assumes all other codes are AS standards
                js["EXPOSURE"] = exposure_environment

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  Chinese Standard CnS ----------------------------------------------------

    class Chinese:
        def __init__(self, name: str, standard:_CreepChineseStandard, fck: float, relative_humidity: float,
                     concrete_age: int, notional_size: float, humidity_type: _CreepChineseHumidityType = "RH",
                     cement_coeff: float = 5, fly_ash_amount: float = 20, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": standard,
                "STR": fck,
                "HU": relative_humidity,
                "AGE": concrete_age,
                "MSIZE": notional_size,
                "HTYPE": humidity_type
            }
            if "JTG" in standard:
                js["BSC"] = cement_coeff
            if standard == "CHINA_JTG3362_2018":
                js["FLYASH"] = fly_ash_amount

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  Korean Standards CnS ----------------------------------------------------

    class Korean:
        def __init__(self, name: str, standard: _CreepKoreanStandard, fck: float, relative_humidity: float,
                     concrete_age: int, notional_size: float, cement_type: _CreepKoreanCementType = "NR",
                     density: float = 240, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": standard,
                "STR": fck,
                "HU": relative_humidity,
                "AGE": concrete_age,
                "MSIZE": notional_size,
                "CTYPE": cement_type
            }
            if standard == "KDS_2016":
                js["DENSITY"] = density

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  PCA CnS -----------------------------------------------------------------

    class PCA:
        def __init__(self, name: str, fck: float, relative_humidity: float, ultimate_creep_strain: float,
                     vol_surface_ratio: float, reinforcement_ratio: float, steel_elasticity_modulus: float,
                     ultimate_shrinkage_strain: float, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "PCA",
                "STR": fck,
                "HU": relative_humidity,
                "UCS": ultimate_creep_strain,
                "VOL": vol_surface_ratio,
                "RR": reinforcement_ratio,
                "MOD": steel_elasticity_modulus,
                "USS": ultimate_shrinkage_strain
            }
            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  Japan CnS ---------------------------------------------------------------

    class Japan:
        def __init__(self, name: str, standard: _CreepJapanStandard , relative_humidity: float, concrete_age: int,
                     vol_surface_ratio: float, cement_content: float, water_content: float, fck: float = 30000,
                     impact_factor: float = 1, age_of_solidification: int = 5, alpha_factor: int = 11,
                     autogenous_shrinkage: bool = True, gamma_factor: int = 1, a_factor: float = 0.1,
                     b_factor: float = 0.7, general_shrinkage: bool = True, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": standard,
                "HU": relative_humidity,
                "AGE": concrete_age,
                "VOL": vol_surface_ratio,
                "CEMCONTENT": cement_content,
                "WATERCONTENT": water_content
            }
            if standard != "JSCE":
                js["STR"] = fck
            if standard == "JSCE_12":
                js["IPFACT"] = impact_factor
                js["AGESOL"] = age_of_solidification
            if standard == "JSCE_07":
                js["ALPHAFACT"] = alpha_factor
                js["bAUTO"] = autogenous_shrinkage
                if autogenous_shrinkage:
                    js["GAMMAFACT"] = gamma_factor
                    js["AFACT"] = a_factor
                    js["BFACT"] = b_factor
                js["bGEN"] = general_shrinkage

            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  Japanese Standard CnS ---------------------------------------------
    class JapaneseStandard:
        def __init__(self, name: str, fck: float, relative_humidity: float, concrete_age: int, notional_size: float,
                     calculation_method: _CreepJapaneseCalMethod = "JSCE", humidity_type: _CreepJapaneseHumidityType = "RH", cement_type: _CreepJapaneseCementType = "NC",
                     environmental_coeff: int = 1, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "JAPAN",
                "STR": fck,
                "HU": relative_humidity,
                "HTYPE": humidity_type,
                "AGE": concrete_age,
                "MSIZE": notional_size,
                "CTYPE": cement_type,
                "CM": calculation_method,
                "LAMBDA": environmental_coeff
            }
            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  User Defined CnS ----------------------------------------------------

    class UserDefined:
        def __init__(self, name: str, shrinkage_func_name: str, creep_func_name: str, creep_age: int, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "CODE": "USER_DEFINED",
                "SSFNAME": shrinkage_func_name,
                "vCREEP_AGE": [
                    {
                        "NAME": creep_func_name,
                        "AGE": creep_age
                    }
                ]
            }
            temp = CreepShrinkage(js, id)
            self.ID = temp.ID
            self.DATA = js

#------------------------------------------ TIME DEPENDENT - COMPRESSIVE STRENGTH ----------------------------------------------------



class CompStrength:
    mats:list['CompStrength'] = []
    ids = []
    def __init__(self,data,id=None):
        if id == None: id =0
        if CompStrength.ids == []: 
            count = 1
        else:
            count = max(CompStrength.ids)+1
        if id == 0 or id in CompStrength.ids: self.ID = count
        if id!= 0 and id not in CompStrength.ids: self.ID = id

        self.DATA = data

        CompStrength.mats.append(self)
        CompStrength.ids.append(self.ID)
    
    @classmethod
    def json(cls):
        json = {"Assign":{}}
        for k in cls.mats:
            json["Assign"][k.ID]=k.DATA
        return json
    
    @staticmethod
    def create():
        MidasAPI("PUT","/db/TDME",CompStrength.json())
        
    @staticmethod
    def get():
        return MidasAPI("GET","/db/TDME")
    
    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/TDME")
        CompStrength.clear()

    @staticmethod
    def clear():
        CompStrength.mats=[]
        CompStrength.ids=[]

    @staticmethod
    def sync():
        a = CompStrength.get()
        if a != {'message': ''}:
            if list(a['TDME'].keys()) != []:
                CompStrength.mats = []
                CompStrength.ids=[]
                for j in a['TDME'].keys():
                    CompStrength(a['TDME'][j], int(j))


    # ---------------------------------  IRC Compressive Strength --------------------------------------------------------------

    class IRC:
        def __init__(self, name: str, code_year: _CompStrengthIRCYear = 2020,
                     fck_delta: float = 0, cement_type: int = 1,
                     aggregate_type: int = 0, id: int = None):

            if id == None: id =0
            # Determine the code name string based on the integer year
            if code_year == 2011 or int(code_year) == 2011:
                code_name = "INDIA(IRC:112-2011)"
            elif code_year == 2000 or int(code_year) == 2000:
                code_name = "INDIA(IRC:18-2000)"
            else: # Default to 2020
                code_name = "INDIA(IRC:112-2020)"

            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": code_name,
                "STRENGTH": fck_delta
            }

            # Add cement and aggregate types for IRC:112 standards
            if (code_year in [2020, 2011]) or (code_year in ['2020','2011']):
                js["iCTYPE"] = cement_type
                js["nAGGRE"] = aggregate_type

            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  ACI Compressive Strength --------------------------------------------------------------

    class ACI:
        def __init__(self, name: str, fck: float = 0, factor_a: float = 1, 
                     factor_b: float = 2, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "ACI",
                "STRENGTH": fck,
                "A": factor_a,
                "B": factor_b
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  CEB-FIP Compressive Strength --------------------------------------------------------------

    class CEB_FIP:
        def __init__(self, name: str, code_year: _CompStrengthCEBFIPYear = 2010, fck: float = 0, 
                     cement_type: int = 1, aggregate_type: int = 0, id: int = None):

            if id == None: id =0
            # Determine code name based on year
            if code_year == 1978 or int(code_year) == 1978:
                code_name = "CEB-FIP(1978)"
            elif code_year == 1990 or int(code_year) == 1990:
                code_name = "CEB-FIP(1990)"
            else:  # Default to 2010
                code_name = "CEB-FIP(2010)"
            
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": code_name,
                "STRENGTH": fck
            }
            
            # Add cement type for 1990 and 2010
            if (code_year in [1990, 2010]) or (code_year in ['1990', '2010']):
                js["iCTYPE"] = cement_type
                
            # Add aggregate type for 2010 only
            if (code_year == 2010) or (code_year == '2010'):
                js["nAGGRE"] = aggregate_type
                
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Ohzagi Compressive Strength --------------------------------------------------------------

    class Ohzagi:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 2, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "Ohzagi",
                "STRENGTH": fck,
                "iCTYPE": cement_type
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  European Compressive Strength --------------------------------------------------------------

    class European:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 2, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "EUROPEAN",
                "STRENGTH": fck,
                "iCTYPE": cement_type
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Russian Compressive Strength --------------------------------------------------------------

    class Russian:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 1, 
                     curing_method: int = 1, concrete_type: int = 1, 
                     max_aggregate_size: float = 0.02, specific_cement_content: float = 0.25, 
                     id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "RUSSIAN",
                "STRENGTH": fck,
                "iCTYPE": cement_type,
                "CMETH": curing_method,
                "CTYPE": concrete_type,
                "MAXS": max_aggregate_size,
                "PZ": specific_cement_content
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Australian Standards Compressive Strength --------------------------------------------------------------
#add EXPOSURE
    class AS:
        def __init__(self, name: str, standard: _CompStrengthASStandard = "AS5100.5-2017", fck: float = 0, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": standard,
                "STRENGTH": fck
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Gilbert and Ranzi Compressive Strength --------------------------------------------------------------

    class GilbertRanzi:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 1, 
                     density: float = 230, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "GILBERT AND RANZI",
                "STRENGTH": fck,
                "iCTYPE": cement_type,
                "DENSITY": density
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Japan Hydration Compressive Strength --------------------------------------------------------------

    class JapanHydration:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 1, 
                     use_concrete_data: bool = True, tensile_strength_factor: float = 3,
                     factor_a: float = 4.5, factor_b: float = 0.95, factor_d: float = 1.11,
                     id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "Japan(hydration)",
                "STRENGTH": fck,
                "iCTYPE": cement_type,
                "bUSE": use_concrete_data,
                "TENS_STRN_FACTOR": tensile_strength_factor
            }
            
            # Add custom factors if not using concrete data
            if not use_concrete_data:
                js.update({
                    "A": factor_a,
                    "B": factor_b,
                    "D": factor_d
                })
                
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  Japan Elastic Compressive Strength --------------------------------------------------------------

    class JapanElastic:
        def __init__(self, name: str, fck: float = 0, elastic_cement_type: int = 0, id: int = None):
 
            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "Japan(elastic)",
                "STRENGTH": fck,
                "iECTYPE": elastic_cement_type
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  KDS-2016 Compressive Strength --------------------------------------------------------------

    class KDS:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 1, 
                     density: float = 230, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "KDS-2016",
                "STRENGTH": fck,
                "iCTYPE": cement_type,
                "DENSITY": density
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js

    # ---------------------------------  KCI-USD12 Compressive Strength --------------------------------------------------------------

    class KCI:
        def __init__(self, name: str, fck: float = 0, cement_type: int = 1, 
                     id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "KCI-USD12",
                "STRENGTH": fck,
                "iCTYPE": cement_type,
                
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js
    # ---------------------------------  Korean Standard Compressive Strength --------------------------------------------------------------

    class KoreanStandard:
        def __init__(self, name: str, fck: float = 0, factor_a: float = 1, 
                     factor_b: float = 2, id: int = None):

            if id == None: id =0
            js = {
                "NAME": name,
                "TYPE": "CODE",
                "CODENAME": "KoreanStandard",
                "STRENGTH": fck,
                "A": factor_a,
                "B": factor_b
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js


    # ---------------------------------  User Defined Compressive Strength --------------------------------------------------------------

    class UserDefined:
        def __init__(self, name: str, scale_factor: float = 1, 
                     time_data: list = None, id: int = None):

            if id == None: id =0
            if time_data is None:
                time_data = [
                    {"TIME": 0, "COMP": 0, "TENS": 0, "ELAST": 0},
                    {"TIME": 1000, "COMP": 30000, "TENS": 1000, "ELAST": 3000000}
                ]
            
            js = {
                "NAME": name,
                "TYPE": "USER",
                "SCALE": scale_factor,
                "aDATA": time_data
            }
            temp = CompStrength(js, id)
            self.ID = temp.ID
            self.DATA = js

#------------------------------------------ TIME DEPENDENT - MATERIAL LINK  ----------------------------------------------------



class TDMatLink:
    mats = {}
    def __init__(self,matID,CnSName='',CompName=''):

        TDMatLink.mats[str(matID)]={
            "TDMT_NAME": CnSName,
            "TDME_NAME": CompName
        }
    
    @classmethod
    def json(cls):
        json = {"Assign": TDMatLink.mats}
        return json
    
    @staticmethod
    def create():
        MidasAPI("PUT","/db/TMAT",TDMatLink.json())
        
    @staticmethod
    def get():
        return MidasAPI("GET","/db/TMAT")
    
    
    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/TMAT")
        TDMatLink.clear()

    @staticmethod
    def clear():
        TDMatLink.mats={}

    @staticmethod
    def sync():
        a = TDMatLink.get()
        if a != {'message': ''}:
            if list(a['TMAT'].keys()) != []:
                TDMatLink.mats = []
                TDMatLink.ids=[]
                for j in a['TMAT'].keys():
                    TDMatLink(a['TMAT'][j], int(j))

#-------------------------------------------------------------------------------------------------
class _ChangeProperty:
    ELEM_ID,TYPE,VALUE = 0,0,0
 

class ChangeProperty:
    data:list[_ChangeProperty] = []
    def __init__(self,elmID:int,notional_size:float=None,vol_srf_rat:float=None):
        ''' ENTER ELEMENT ID and corresponding value '''
        self.ELEM_ID = elmID
        self.TYPE = "NSM"
        self.VALUE = 0
        if notional_size:
            self.TYPE = "NSM"
            self.VALUE = notional_size
        if vol_srf_rat:
            self.TYPE = "VSR"
            self.VALUE = vol_srf_rat

        ChangeProperty.data.append(self)

    @classmethod
    def json(cls):
        json = {"Assign": {}}
        for dat in cls.data:
            json["Assign"][dat.ELEM_ID] = { "TYPE": dat.TYPE, "H_VS": dat.VALUE }
        return json
    
    @classmethod
    def create(cls):
        MidasAPI("PUT","/db/EDMP",cls.json())
        
    @staticmethod
    def get():
        return MidasAPI("GET","/db/EDMP")
    
    
    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/EDMP")
        TDMatLink.clear()

    @staticmethod
    def clear():
        ChangeProperty.data=[]

#-------------------------------------------------------------------------------------------------