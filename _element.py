from ._mapi import MidasAPI,NX
from ._node import Node,nodeByID,nodesInGroup
from ._group import _add_node_2_stGroup,Group, _add_elem_2_stGroup
import numpy as np
from math import hypot,ceil
from ._utils import _convItem2List , _longestList,sFlatten
from typing import Literal
from ._material import Material
from ._section import Section
_meshType = Literal['Quad','Tri']
_extrudeInp = Literal['XYZ','NODE_ID']
_order = Literal['ID','XYZ','XZY','YXZ','YZX','ZXY','ZYX']


_location2Index = {
    'XYZ' : (0,1,2),
    'XZY' : (0,2,1),
    'YXZ' : (1,0,2),
    'YZX' : (1,2,0),
    'ZXY' : (2,0,1),
    'ZYX' : (2,1,0),
}

def _cell(point): #SIZE OF GRID - string format
    return str(f"{int(point[0])},{int(point[1])},{int(point[2])}")

def _SInterp(angle,num_points):
    from scipy.interpolate import interp1d , Akima1DInterpolator
    angle = _convItem2List(angle)
    if len(angle) == 1 : 
        angle.append(angle[0])
        angle.append(angle[0])
    if len(angle) == 2 : 
        angle.append(angle[-1])
        angle[1] = (angle[0]+angle[2])*0.5

    num_angle = len(angle)
    angle_intrp_x = [0]
    angle_intrp_y = [angle[0]]
    for a in range(num_angle-1):
        angle_intrp_x.append((a+1)*(num_points-1)/(num_angle-1))
        angle_intrp_y.append(angle[a+1])

    _alignment = Akima1DInterpolator(angle_intrp_x, angle_intrp_y,method='makima')
    angle_intrp_func = interp1d(angle_intrp_x, angle_intrp_y)

    angle_intrp_finalY = []
    for i in range(num_points):
        angle_intrp_finalY.append(_alignment(i))

    return angle_intrp_finalY

def _interpolateAlignment(pointsArray,n_seg=10,deg=1,mSize=0,includePoint:bool=True,div_axis="L") -> list:
    from scipy.interpolate import splev, splprep
    pointsArray = np.array(pointsArray)
    x_p, y_p , z_p  = pointsArray[:,0] , pointsArray[:,1] , pointsArray[:,2]

    if deg < 1 :
        deg = 1
    if deg > len(pointsArray)-1:
        deg = len(pointsArray)-1

    #-- Actual length ----

    tck, u = splprep([x_p, y_p, z_p], s=0, k=deg)

    u_fine = np.linspace(0, 1, 500)
    x_den, y_den, z_den = splev(u_fine, tck)

    dx = np.diff(x_den)
    dy = np.diff(y_den)
    dz = np.diff(z_den)
    dl=[]
    for i in range(len(dx)):
        dl.append(hypot(dx[i],dy[i],dz[i]))

    cum_l = np.insert(np.cumsum(dl),0,0)
    total_l = cum_l[-1]


    if n_seg==0 or mSize!=0:
        n_seg=int(total_l/mSize)


    if div_axis == "X":
        eq_x = np.linspace(x_p[0],x_p[-1],n_seg+1)
        interp_u = np.interp(eq_x,x_den,u_fine)
    elif div_axis == "Y":
        eq_y = np.linspace(y_p[0],y_p[-1],n_seg+1)
        interp_u = np.interp(eq_y,y_den,u_fine)
    elif div_axis == "Z":
        eq_z = np.linspace(z_p[0],z_p[-1],n_seg+1)
        interp_u = np.interp(eq_z,z_den,u_fine)
    else :
        eq_len = np.linspace(0,total_l,n_seg+1)
        interp_u = np.interp(eq_len,cum_l,u_fine)


    if includePoint:
        interp_u = np.sort(np.append(interp_u,u[1:-1])).tolist()

        eq_u = 1/n_seg # for filtering close points
    
        new_u = []
        skip=0
        for i in range(len(interp_u)-1):
            if skip == 1:
                skip = 0 
                continue
            if interp_u[i+1]-interp_u[i] < 0.2*eq_u:
                if interp_u[i] in u:
                    new_u.append(interp_u[i])
                    skip=1
                else:
                    new_u.append(interp_u[i+1])
                    skip=1
            else:
                new_u.append(interp_u[i])
        new_u.append(interp_u[-1])
    else:
        new_u = interp_u


    interp_x, interp_y , interp_z = splev(new_u, tck)


    align_fine_points  = [ [round(x,6), round(y,6), round(z,6)] for x, y, z in zip(interp_x, interp_y , interp_z) ]

    return align_fine_points



def _nodeDIST(a:Node,b:Node):
    return round(hypot((a.X-b.X),(a.Y-b.Y),(a.Z-b.Z)),6)

def _nodeAngleVector(b:Node,a:Node):

    Z_new = np.array([0.000001,0,1])
    X_new = np.array([(a.X-b.X),(a.Y-b.Y),(a.Z-b.Z)])
    Y_new = np.cross(Z_new, X_new)

    Z_new = np.cross(X_new, Y_new) # Recomputing

    X_new = X_new / (np.linalg.norm(X_new)+0.000001)
    Y_new = Y_new / (np.linalg.norm(Y_new)+0.000001)
    Z_new = Z_new / (np.linalg.norm(Z_new)+0.000001)


    return [X_new,Y_new,Z_new]


def _triangleAREA(a:Node,b:Node,c:Node):
    v1 = np.array([a.X-b.X,a.Y-b.Y,a.Z-b.Z])
    v2 = np.array([b.X-c.X,b.Y-c.Y,b.Z-c.Z])
    mag = np.linalg.norm(np.cross(v1, v2))
    return float(0.5 * mag) , np.cross(v1, v2)/mag

def _calcVector(deltaLocation,angle=0): # Returns normalised local X,Y,Z for line
    Z_new = np.array([0.000001,0,1])
    X_new = np.array(deltaLocation)
    Y_new = np.cross(Z_new, X_new)

    Z_new = np.cross(X_new, Y_new) # Recomputing

    X_new = X_new / (np.linalg.norm(X_new)+0.000001)
    Y_new = Y_new / (np.linalg.norm(Y_new)+0.000001)
    Z_new = Z_new / (np.linalg.norm(Z_new)+0.000001)

    from scipy.spatial.transform import Rotation as R
    p_y = np.array(Y_new)
    p_z = np.array(Z_new)

    axis = np.array(X_new)
    theta = np.deg2rad(angle)               # or radians directly
    rot = R.from_rotvec(axis * theta)           # axis-angle as rotation vector
    
    rt_y = rot.apply(p_y)                         # rotated point around axis through origin
    rt_z = rot.apply(p_z)  
    
    return [X_new,rt_y,rt_z]

def _rotatePT(pt,axis,deg):
    from scipy.spatial.transform import Rotation as R
    p = np.array(pt)
    axis = np.array(axis)
    theta = np.deg2rad(deg)               # or radians directly
    rot = R.from_rotvec(axis * theta)           # axis-angle as rotation vector
    return rot.apply(p)                         # rotated point around axis through origin

def _pointOffset(pts,yEcc=0,zEcc=0,angle=0):
    from ._utils import _matchArray

    angle2 = _matchArray(pts,angle)
    yEcc2 = _matchArray(pts,yEcc)
    zEcc2 = _matchArray(pts,zEcc)

    norm = []
    norm.append(_calcVector(np.subtract(pts[1],pts[0]),angle2[0]))    # first X- along vector

    for i in range(len(pts)-2): # Averaged X- along vector for middle points
        X_new1 = np.array(np.subtract(pts[i+1],pts[i]))
        X_new2 = np.array(np.subtract(pts[i+2],pts[i+1]))

        X_new1 = X_new1 / (np.linalg.norm(X_new1)+0.000001)
        X_new2 = X_new2 / (np.linalg.norm(X_new2)+0.000001)

        norm.append(_calcVector(np.add(X_new1,X_new2),angle2[i+1]))

    norm.append(_calcVector(np.subtract(pts[-1],pts[-2]),angle2[-1])) # last X- along vector

    # print(norm)

    pt_new = []
    for i in range(len(pts)):
        pt_new.append(pts[i]+yEcc2[i]*norm[i][1]+zEcc2[i]*norm[i][2])

    return pt_new


def _ADD(self):

    # ------------  ID assignment -----------------------
    if NX.onlyNode == False :
        id = int(self.ID)
        # if not Element.ids:
        #     count = 1
        # else:
        #     count = max(Element.ids) + 1

        count = Element.maxID+1
        if id == 0:
            self.ID = count
            Element.elements.append(self)
            Element.ids.append(int(self.ID))
            Element.maxID+= 1
        elif id in Element.ids:
            self.ID = int(id)
            print(f'⚠️  Element with ID {id} already exists! It will be replaced.')
            index = Element.ids.index(id)
            Element.elements[index] = self
        else:
            self.ID = id
            Element.elements.append(self)
            Element.ids.append(int(self.ID))
            if id > Element.maxID:
                Element.maxID = id
        Element.__elemDIC__[str(self.ID)] = self
        cell_loc = _cell(self.CENTER)
        
        if cell_loc in Element.Grid:
            Element.Grid[cell_loc].append(self)
        else:
            Element.Grid[cell_loc]=[]
            Element.Grid[cell_loc].append(self)
        
        # ------------  Group assignment -----------------------
        if self._GROUP == "" :
            pass
        elif isinstance(self._GROUP, list):
            for gpName in self._GROUP:
                _add_elem_2_stGroup(self.ID,gpName)
                # for nd in self.NODE:
                _add_node_2_stGroup(self.NODE,gpName)
        elif isinstance(self._GROUP, str):
            _add_elem_2_stGroup(self.ID,self._GROUP)
            # for nd in self.NODE:
            _add_node_2_stGroup(self.NODE,self._GROUP)

        
        if isinstance(self.MATL,str):
            self.MATL = Material._dic.get(self.MATL,99)

        if isinstance(self.SECT,str):
            self.SECT = Section._dic.get(self.SECT,99)


    else:
        if self._GROUP == "" :
            pass
        elif isinstance(self._GROUP, list):
            for gpName in self._GROUP:
                for nd in self.NODE:
                    _add_node_2_stGroup(nd,gpName)
        elif isinstance(self._GROUP, str):
            for nd in self.NODE:
                _add_node_2_stGroup(nd,self._GROUP)
            





def _updateElem(self):
    js2s = {'Assign': {self.ID: _Obj2JS(self)}}
    MidasAPI('PUT', '/db/elem', js2s)
    return js2s

def _Obj2JS(obj):
    # Base attributes common to many elements
    js = {
        "TYPE": obj.TYPE,
        "MATL": obj.MATL,
        "SECT": obj.SECT,
        "NODE": obj.NODE,
    }
    
    # Add optional attributes if they exist on the object
    if hasattr(obj, 'ANGLE'): js["ANGLE"] = obj.ANGLE
    if hasattr(obj, 'STYPE'): js["STYPE"] = obj.STYPE
    
    # Handle type-specific and subtype-specific attributes
    if obj.TYPE == 'TENSTR': # Tension/Hook/Cable
        # Tension-only (stype=1) - can have TENS parameter
        if obj.STYPE == 1:
            if hasattr(obj, 'TENS'): js["TENS"] = obj.TENS
            if hasattr(obj, 'T_LIMIT'): js["T_LIMIT"] = obj.T_LIMIT
            if hasattr(obj, 'T_bLMT'): js["T_bLMT"] = obj.T_bLMT
        
        # Hook (stype=2) - has NON_LEN parameter
        elif obj.STYPE == 2:
            if hasattr(obj, 'NON_LEN'): js["NON_LEN"] = obj.NON_LEN
        
        # Cable (stype=3) - has CABLE, NON_LEN, and TENS parameters
        elif obj.STYPE == 3:
            if hasattr(obj, 'CABLE'): js["CABLE"] = obj.CABLE
            if hasattr(obj, 'NON_LEN'): js["NON_LEN"] = obj.NON_LEN
            if hasattr(obj, 'TENS'): js["TENS"] = obj.TENS

    elif obj.TYPE == 'COMPTR': # Compression/Gap
        # Compression-only (stype=1) - can have TENS, T_LIMIT, T_bLMT
        if obj.STYPE == 1:
            if hasattr(obj, 'TENS'): js["TENS"] = obj.TENS
            if hasattr(obj, 'T_LIMIT'): js["T_LIMIT"] = obj.T_LIMIT
            if hasattr(obj, 'T_bLMT'): js["T_bLMT"] = obj.T_bLMT
        
        # Gap (stype=2) - has NON_LEN parameter
        elif obj.STYPE == 2:
            if hasattr(obj, 'NON_LEN'): js["NON_LEN"] = obj.NON_LEN

    elif obj.TYPE == 'WALL': # Wall
            js["WALL"] = obj.WID
            js["W_TYPE"] = obj.WTYPE
            js["W_CON"] = 0


    return js

def _JS2Obj(id, js):
    elem_type = js.get('TYPE')
    
    # Prepare arguments for constructors
    args = {
        'id': int(id),
        'mat': js.get('MATL'),
        'sect': js.get('SECT'),
        'node': js.get('NODE'),
        'angle': js.get('ANGLE'),
        'stype': js.get('STYPE')
    }

    args['node'] = [x for x in args['node'] if x != 0]
    nNodes = len(args['node'])
    # Prepare individual parameters for optional/subtype-specific parameters
    non_len = js.get('NON_LEN')
    cable_type = js.get('CABLE')
    tens = js.get('TENS')
    t_limit = js.get('T_LIMIT')

    #Wall type
    w_type = js.get('W_TYPE')
    w_id = js.get('WALL')

    if elem_type == 'BEAM':
        Element.Beam(args['node'][0], args['node'][1], args['mat'], args['sect'], args['angle'], '', args['id'])
    elif elem_type == 'TRUSS':
        Element.Truss(args['node'][0], args['node'][1], args['mat'], args['sect'], args['angle'],'',  args['id'])
    elif elem_type == 'PLATE':
        Element.Plate(args['node'][:nNodes], args['stype'], args['mat'], args['sect'], args['angle'], '', args['id'])
    elif elem_type == 'WALL':
        Element.Wall(args['node'][:nNodes], args['stype'],w_type,w_id, args['mat'], args['sect'], '', args['id'])
    elif elem_type == 'TENSTR':
        Element.Tension(args['node'][0], args['node'][1], args['stype'], args['mat'], args['sect'], args['angle'], '', args['id'], non_len, cable_type, tens, t_limit)
    elif elem_type == 'COMPTR':
        Element.Compression(args['node'][0], args['node'][1], args['stype'], args['mat'], args['sect'], args['angle'], '', args['id'], tens, t_limit, non_len)
    elif elem_type == 'SOLID':
        Element.Solid(nodes=args['node'][:nNodes], mat=args['mat'],group='', id=args['id'])


class _helperELEM:
    ID, TYPE, MATL,SECT,NODE,ANGLE,LENGTH,STYPE,AREA,NORMAL,CENTER,LOCALX,LOCALY,LOCALZ = 0,0,0,0,0,0,0,0,0,0,0,0,0,0
class _common:
    def __str__(self):
        return str(f'ID = {self.ID} \nJSON : {_Obj2JS(self)}\n')

    def update(self):
        return _updateElem(self)

# --- Main Element Class ---
class Element():
    elements:list[_helperELEM] = []
    ids:list[int] = []
    maxID:int = 0
    __elemDIC__ = {}
    Grid ={}    # Node object in cube grid

    
    lastLoc = (0,0,0) #Last Location created using Beam element

    @staticmethod
    def _deleteElem(eID):
        if str(eID) in Element.__elemDIC__:
            eObj = elemByID(eID)
            cell_loc = _cell(eObj.CENTER)
            Element.elements.remove(eObj)
            Element.ids.remove(eID)
            Element.__elemDIC__.pop(str(eID))
            Element.Grid[cell_loc].remove(eObj)
            
            

    @classmethod
    def json(cls):
        # if _quadShape.shapes!=[]: Element.Plate.__meshShapes()
        json_data = {"Assign": {}}
        for elem in cls.elements:
            js = _Obj2JS(elem)
            json_data["Assign"][elem.ID] = js
        return json_data

    @classmethod
    def create(cls):
        if cls.elements:
            __maxNos__ = 20_000  #20_000 elements can be sent in a single request
            __numItem__ = len(cls.elements)
            __nTime__ = int(__numItem__/__maxNos__)+1

            if __nTime__ == 1:
                MidasAPI("PUT", "/db/ELEM", Element.json())
            else:
                __remainItem__ = __numItem__
                for n in range(__nTime__):
                    json = {"Assign":{}}
                    __nElem_c__ = min(__maxNos__,__remainItem__)
                    for q in range(__nElem_c__):
                        elem=cls.elements[n*__maxNos__+q]
                        js = _Obj2JS(elem)
                        json["Assign"][elem.ID] = js
                    MidasAPI("PUT","/db/ELEM",json)
                    __remainItem__ -= __maxNos__
        

    @staticmethod
    def get():
        return MidasAPI("GET", "/db/ELEM")

    @staticmethod
    def sync():
        if Node.nodes == []:
            Node.sync()
        a = Element.get()
        if a and 'ELEM' in a and a['ELEM']:
            Element.clear()
            for elem_id, data in a['ELEM'].items():
                _JS2Obj(elem_id, data)

    @staticmethod
    def delete():
        MidasAPI("DELETE", "/db/ELEM")
        Element.clear()
    
    @staticmethod
    def clear():
        Element.elements = []
        Element.ids = []
        Element.__elemDIC__={}
        Element.maxID = 0

    # --- Element Type Subclasses ---
    class Wall(_common):
        def __init__(self, nodes: list, stype: int = 2, wtype:int = 0, wID:int = 1,mat: int = 1, sect: int = 1, group = "" , id: int = None):

            if id == None: id =0
            self.ID = id
            self.TYPE = 'WALL'
            self.MATL = mat
            self.SECT = sect
            
            self.STYPE = stype  #  1. Membrane or  2. Plate
            self.WTYPE = wtype  #  0. Plate Base,  1. CRB-Pin ,  2. CRB-Fix
            self.WID = wID  
            self._GROUP = group


            self.NODE = nodes
            _n1 = nodeByID(nodes[0])
            _n2 = nodeByID(nodes[1])
            _n3 = nodeByID(nodes[2])
            _n4 = nodeByID(nodes[3])
            a1 , n1 = _triangleAREA(_n1,_n2,_n3)
            a2 , n2 = _triangleAREA(_n3,_n4,_n1)
            self.AREA = a1+a2
            self.NORMAL = (n1+n2)/np.linalg.norm((n1+n2+0.000001))
            self.CENTER = np.average([_n1.LOC,_n2.LOC,_n3.LOC,_n4.LOC],0)
                

            _ADD(self)


    class Beam(_common):

        def __init__(self, i: int, j: int, mat: int = 1, sect: int = 1, angle: float = 0, group:str = "" , id: int = None,bLocalAxis:bool=False):

            if id == None: id =0
            self.ID = id
            self.TYPE = 'BEAM'
            self.MATL = mat
            self.SECT = sect
            self.NODE = [i, j]
            self.ANGLE = angle
            self._GROUP = group
            
            _n1 = nodeByID(i)
            _n2 = nodeByID(j)
            self.LENGTH = _nodeDIST(_n1,_n2)
            self.CENTER = np.average([_n1.LOC,_n2.LOC],0)
            _dirVect = np.subtract(_n2.LOC,_n1.LOC)
            self.LOCALX = np.round(_dirVect/(np.linalg.norm(_dirVect)),4)
            _tempZ = (0.00001,0,1)
            _LOCALY = np.cross(_tempZ,self.LOCALX)
            _ROTLY = _rotatePT(_LOCALY,self.LOCALX,angle)

            self.LOCALY = np.round(_ROTLY / np.linalg.norm(_ROTLY),4)

            _LOCALZ = np.cross(self.LOCALX, self.LOCALY)
            self.LOCALZ = np.round(_LOCALZ / np.linalg.norm(_LOCALZ),4)

            if bLocalAxis:
                _tempAngle = _nodeAngleVector(_n1,_n2)
                _n1.AXIS = np.add(_n1.AXIS,_tempAngle)
                _n2.AXIS = np.add(_n2.AXIS,_tempAngle)

                _norm1 = np.linalg.norm(_n1.AXIS ,axis=1,keepdims=True)
                _n1.AXIS = _n1.AXIS /_norm1

                _norm2 = np.linalg.norm(_n2.AXIS ,axis=1,keepdims=True)
                _n2.AXIS = _n2.AXIS /_norm2

            Element.lastLoc = (_n2.X,_n2.Y,_n2.Z)

            _ADD(self)

        @staticmethod
        def SDL(s_loc:list,dir:list,l:float,n:int=1,mat:int=1,sect:int=1,angle:float=0, group:str = "" , id: int = None,bLocalAxis:bool=False): #CHANGE TO TUPLE
                if id == None: id =0
                if isinstance(s_loc,Node):
                    s_loc = (s_loc.X,s_loc.Y,s_loc.Z)

                beam_nodes =[]
                beam_obj = []
                s_locc = np.array(s_loc)
                unit_vec = np.array(dir)/np.linalg.norm(dir)

                for i in range(n+1):
                    locc = s_locc+i*l*unit_vec/n
                    Enode=Node(locc[0].item(),locc[1].item(),locc[2].item())
                    beam_nodes.append(Enode.ID)
                Element.lastLoc = (locc[0].item(),locc[1].item(),locc[2].item())
                for i in range(n):
                    if id == 0 : id_new = 0
                    else: id_new = id+i
                    beam_obj.append(Element.Beam(beam_nodes[i],beam_nodes[i+1],mat,sect,angle,group,id_new,bLocalAxis))
                
                return beam_obj
                    

        @staticmethod
        def SE(s_loc:list,e_loc:list,n:int=1,mat:int=1,sect:int=1,angle:float=0, group:str = "" , id: int = None,bLocalAxis:bool=False):
                if id == None: id =0
                if isinstance(s_loc,Node):
                    s_loc = (s_loc.X,s_loc.Y,s_loc.Z)
                if isinstance(e_loc,Node):
                    e_loc = (e_loc.X,e_loc.Y,e_loc.Z)

                beam_nodes =[]
                beam_obj = []
                i_loc = np.linspace(s_loc,e_loc,n+1)
                for i in range(n+1):
                    Enode=Node(i_loc[i][0].item(),i_loc[i][1].item(),i_loc[i][2].item())
                    beam_nodes.append(Enode.ID)
                for i in range(n):
                    if id == 0 : id_new = 0
                    else: id_new = id+i
                    beam_obj.append(Element.Beam(beam_nodes[i],beam_nodes[i+1],mat,sect,angle,group,id_new,bLocalAxis))
                
                return beam_obj
        
        @staticmethod
        def PLine(points_loc: list, n_div: int = 0, deg: int = 1, includePoint: bool = False,
                  mat: int = 1, sect: int = 1, angle: list[float] = 0,
                  group: str = "", id: int = None, bLocalAxis: bool = False,
                  div_axis: Literal['X','Y','Z','L'] = "L"):
            
            if id == None: id = 0
            beam_nodes = []
            beam_obj = []
            if n_div == 0:
                i_loc = points_loc
            else:
                i_loc = _interpolateAlignment(points_loc, n_div, deg, 0, includePoint, div_axis)

            num_points = len(i_loc)
            angle_intrp_finalY = _SInterp(angle, num_points - 1)  # Beta Angle applied to Elements, so n-1

            for i in i_loc:
                Enode = Node(i[0], i[1], i[2])
                beam_nodes.append(Enode.ID)
            for i in range(len(i_loc) - 1):
                if id == 0: id_new = 0
                else: id_new = id + i
                beam_obj.append(Element.Beam(beam_nodes[i], beam_nodes[i+1], mat, sect, angle_intrp_finalY[i].item(), group, id_new, bLocalAxis))

            return beam_obj
        
        @staticmethod
        def PLine2(points_loc: list, n_div: int = 0, deg: int = 1, includePoint: bool = False,
                   mat: int = 1, sect: int = 1, angle: list[float] = 0,
                   group: str = "", id: int = None, bLocalAxis: bool = False,
                   div_axis: Literal['X','Y','Z','L'] = "L",
                   yEcc: list[float] = 0, zEcc: list[float] = 0,
                   bAngleInEcc: bool = True):
            
            from ._utils import _matchArray
            if id == None: id = 0
            beam_nodes = []
            beam_obj = []
            if n_div == 0:
                i_loc = points_loc
            else:
                i_loc = _interpolateAlignment(points_loc, n_div, deg, 0, includePoint, div_axis)

            num_points = len(i_loc)
            if bAngleInEcc:
                angle_intrp_Ecc = _SInterp(angle, num_points)
            else:
                angle_intrp_Ecc = _matchArray(i_loc, [0])
            angle_intrp_finalY = _SInterp(angle, num_points - 1)  # Beta Angle applied to Elements, so n-1

            yEcc_intrp = _SInterp(yEcc, num_points)
            zEcc_intrp = _SInterp(zEcc, num_points)

            i_loc2 = _pointOffset(i_loc, yEcc_intrp, zEcc_intrp, angle_intrp_Ecc)
            for i in i_loc2:
                Enode = Node(i[0], i[1], i[2])
                beam_nodes.append(Enode.ID)

            for i in range(len(i_loc2) - 1):
                if id == 0: id_new = 0
                else: id_new = id + i
                beam_obj.append(Element.Beam(beam_nodes[i], beam_nodes[i+1], mat, sect, angle_intrp_finalY[i].item(), group, id_new, bLocalAxis))

            return beam_obj

    class Truss(_common):
        def __init__(self, i: int, j: int, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None):
           
            if id == None: id =0
            self.ID = id
            self.TYPE = 'TRUSS'
            self.MATL = mat
            self.SECT = sect
            self.NODE = [i, j]
            self.ANGLE = angle
            self._GROUP = group
            _n1 = nodeByID(i)
            _n2 = nodeByID(j)
            self.LENGTH = _nodeDIST(_n1,_n2)
            self.CENTER = np.average([_n1.LOC,_n2.LOC],0)
            _dirVect = np.subtract(_n2.LOC,_n1.LOC)
            self.LOCALX = np.round(_dirVect/(np.linalg.norm(_dirVect)),4)
            _tempZ = (0.00001,0,1)
            _LOCALY = np.cross(_tempZ,self.LOCALX)
            _ROTLY = _rotatePT(_LOCALY,self.LOCALX,angle)

            self.LOCALY = np.round(_ROTLY / np.linalg.norm(_ROTLY),4)

            _LOCALZ = np.cross(self.LOCALX, self.LOCALY)
            self.LOCALZ = np.round(_LOCALZ / np.linalg.norm(_LOCALZ),4)

            Element.lastLoc = (_n2.X,_n2.Y,_n2.Z)
            _ADD(self)

        @staticmethod
        def SDL(s_loc:list,dir:list,l:float,n:int=1,mat:int=1,sect:int=1,angle:float=0, group = "" , id: int = None):
            if id == None: id =0
            if isinstance(s_loc,Node):
                    s_loc = (s_loc.X,s_loc.Y,s_loc.Z)

            beam_nodes =[]
            beam_obj =[]
            s_locc = np.array(s_loc)
            unit_vec = np.array(dir)/np.linalg.norm(dir)

            for i in range(n+1):
                locc = s_locc+i*l*unit_vec/n
                Enode=Node(locc[0].item(),locc[1].item(),locc[2].item())
                beam_nodes.append(Enode.ID)
            
            for i in range(n):
                if id == 0 : id_new = 0
                else: id_new = id+i
                beam_obj.append(Element.Truss(beam_nodes[i],beam_nodes[i+1],mat,sect,angle,group,id_new))
            
            return beam_obj
                

        @staticmethod
        def SE(s_loc:list,e_loc:list,n:int=1,mat:int=1,sect:int=1,angle:float=0, group = "" , id: int = None):
            if id == None: id =0
            if isinstance(s_loc,Node):
                s_loc = (s_loc.X,s_loc.Y,s_loc.Z)
            if isinstance(e_loc,Node):
                e_loc = (e_loc.X,e_loc.Y,e_loc.Z)

            beam_nodes =[]
            beam_obj = []
            i_loc = np.linspace(s_loc,e_loc,n+1)
            for i in range(n+1):
                Enode=Node(i_loc[i][0].item(),i_loc[i][1].item(),i_loc[i][2].item())
                beam_nodes.append(Enode.ID)
            
            for i in range(n):
                if id == 0 : id_new = 0
                else: id_new = id+i
                beam_obj.append(Element.Truss(beam_nodes[i],beam_nodes[i+1],mat,sect,angle,group,id_new))
            
            return beam_obj 
          
    class Plate(_common):
        def __init__(self, nodes: list, stype: int = 1, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None):
            if id == None: id =0
            self.ID = id
            self.TYPE = 'PLATE'
            self.MATL = mat
            self.SECT = sect
            
            self.ANGLE = angle
            self.STYPE = stype
            self._GROUP = group

            uniq_nodes = list(dict.fromkeys(nodes))
            self._NPOINT=len(uniq_nodes)
            if len(uniq_nodes)==3:
                self.NODE = uniq_nodes
                _n1 = nodeByID(uniq_nodes[0])
                _n2 = nodeByID(uniq_nodes[1])
                _n3 = nodeByID(uniq_nodes[2])
                self.CENTER = np.average([_n1.LOC,_n2.LOC,_n3.LOC],0)
                self.AREA,self.NORMAL = _triangleAREA(_n1,_n2,_n3)

                # NEW CODE FOR LOCAL AXIS OF PLATES
                self.LOCALZ = np.round(self.NORMAL,4)

                _dirVect = np.subtract(_n2.LOC,_n1.LOC)
                _LOCALX = _dirVect/(np.linalg.norm(_dirVect))
                self.LOCALX = np.round(_rotatePT(_LOCALX,self.LOCALZ,angle),4)
                self.LOCALY = np.round(np.cross(self.LOCALZ , self.LOCALX),4)

            elif len(uniq_nodes)==4:
                self.NODE = nodes
                _n1 = nodeByID(uniq_nodes[0])
                _n2 = nodeByID(uniq_nodes[1])
                _n3 = nodeByID(uniq_nodes[2])
                _n4 = nodeByID(uniq_nodes[3])
                a1 , n1 = _triangleAREA(_n1,_n2,_n3)
                a2 , n2 = _triangleAREA(_n3,_n4,_n1)
                self.AREA = a1+a2
                self.NORMAL = np.round((n1+n2)/np.linalg.norm((n1+n2+0.000001)),4)
                self.CENTER = np.average([_n1.LOC,_n2.LOC,_n3.LOC,_n4.LOC],0)

                # NEW CODE FOR LOCAL AXIS OF PLATES
                self.LOCALZ = self.NORMAL

                _dirVect1 = np.subtract(_n2.LOC,_n1.LOC)
                _dirVect2 = np.subtract(_n3.LOC,_n4.LOC)
                _LOCALX = np.round((_dirVect1+_dirVect2)/np.linalg.norm((_dirVect1+_dirVect2)),4)
                self.LOCALX = np.round(_rotatePT(_LOCALX,self.LOCALZ,angle),4)
                self.LOCALY = np.round(np.cross(self.LOCALZ , self.LOCALX),4)
                


            _ADD(self)

        
        @staticmethod
        def loftGroups(strGroups: list, stype: int = 1, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None,nDiv:int=1,bClose:bool=False): #CHANGE TO TUPLE
                # INPUTS 2 or more structure groups to create rectangular plates between the nodes | No. of nodes should be same in the Str Group
            id_new = None
            n_groups = len(strGroups)
            if n_groups < 2 :
                print("⚠️ No. of structure groups in Plate.loftGroups in less than 2")
                return False
            plate_obj = []
            for ng in range(n_groups-1):
                nID_A = nodesInGroup(strGroups[ng])   
                nID_B = nodesInGroup(strGroups[ng+1])
                if bClose:
                    nID_A.append(nID_A[0])
                    nID_B.append(nID_B[0])

                max_len = max(len(nID_A),len(nID_B))
                if max_len < 2 :
                    print("⚠️ No. of nodes in Plate.loftGroups in less than 2")
                    return False

                nID_A , nID_B = _longestList(nID_A , nID_B)

                if nDiv == 1 :
                    for i in range(max_len-1):
                        if id != None : id_new = id+i
                        pt_array = [nID_A[i],nID_B[i],nID_B[i+1],nID_A[i+1]]
                        plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id_new))
                if nDiv > 1 :
                    nID_dic = {}
                    for j in range(nDiv+1):
                        nID_dic[j] = []
                    nID_dic[0] = nID_A
                    nID_dic[nDiv] = nID_B
                    for i in range(max_len):
                        loc0= nodeByID(nID_A[i]).LOC
                        loc1 = nodeByID(nID_B[i]).LOC
                        int_points = np.linspace(loc0,loc1,nDiv+1)

                        for j in range(nDiv-1):
                            nID_dic[j+1].append(Node(int_points[j+1][0],int_points[j+1][1],int_points[j+1][2]).ID)
                    j=0
                    for q in range(nDiv):
                        for i in range(max_len-1):
                            if id != None : id_new = id+j
                            pt_array = [nID_dic[q][i],nID_dic[q+1][i],nID_dic[q+1][i+1],nID_dic[q][i+1]]
                            plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id))
                            j+=1

            return plate_obj
        
        @staticmethod
        def extrude(inpType:_extrudeInp,input: list,dir:list,nDiv:int=1,bClose:bool=False, stype: int = 1, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None): #CHANGE TO TUPLE
                # INPUTS 2 or more structure groups to create rectangular plates between the nodes | No. of nodes should be same in the Str Group
            nDiv = int(nDiv)
            nID_A = []
            nID_B = []

            def _createPlateExtrude(nID_A,nID_B,nDiv,id):
                max_len = len(nID_B)
                id_new = None
                plate_obj = []
                if nDiv == 1 :
                    for i in range(max_len-1):
                        if id != None : id_new = id+i
                        pt_array = [nID_A[i],nID_B[i],nID_B[i+1],nID_A[i+1]]
                        plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id_new))
                if nDiv > 1 :
                    nID_dic = {}
                    for j in range(nDiv+1):
                        nID_dic[j] = []
                    nID_dic[0] = nID_A
                    nID_dic[nDiv] = nID_B
                    for i in range(max_len):
                        loc0= nodeByID(nID_A[i]).LOC
                        loc1 = nodeByID(nID_B[i]).LOC
                        int_points = np.linspace(loc0,loc1,nDiv+1)

                        for j in range(nDiv-1):
                            nID_dic[j+1].append(Node(int_points[j+1][0],int_points[j+1][1],int_points[j+1][2]).ID)
                    j=0
                    for q in range(nDiv):
                        for i in range(max_len-1):
                            if id != None : id_new = id+j
                            pt_array = [nID_dic[q][i],nID_dic[q+1][i],nID_dic[q+1][i+1],nID_dic[q][i+1]]
                            plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id_new))
                            j+=1

                return plate_obj


            if inpType == 'XYZ':
                points = input

                f_pt = np.add(points,dir)

                for i,pt in enumerate(points):
                    nID_A.append(Node(pt[0],pt[1],pt[2]).ID)
                    nID_B.append(Node(f_pt[i][0],f_pt[i][1],f_pt[i][2]).ID)

                if bClose:
                    nID_A.append(nID_A[0])
                    nID_B.append(nID_B[0])

                return _createPlateExtrude(nID_A,nID_B,nDiv,id)

            elif inpType == 'NODE_ID':
                points = input
                nID_A = list(points)
                pts_loc = [nodeByID(pt).LOC for pt in points]

                f_pt = np.add(pts_loc,dir)

                for i in range(len(points)):
                    nID_B.append(Node(f_pt[i][0],f_pt[i][1],f_pt[i][2]).ID)

                if bClose:
                    nID_A.append(nID_A[0])
                    nID_B.append(nID_B[0])

                return _createPlateExtrude(nID_A,nID_B,nDiv,id)
            
            
            # if inpType in ('NODE_ID','XYZ'):
            #     return _createPlateExtrude(nID_A,nID_B,nDiv,id)
            
        @staticmethod
        def extrudeLine(elmIDs: list,dir:list,nDiv:int=1,bDeleteLine:bool=False, stype: int = 1, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None): #CHANGE TO TUPLE
                # INPUTS 2 or more structure groups to create rectangular plates between the nodes | No. of nodes should be same in the Str Group
            nDiv = int(nDiv)
            nID_A = []
            nID_B = []

            def _createPlateExtrude(nID_A,nID_B,nDiv,id):
                max_len = len(nID_B)
                id_new = None
                plate_obj = []
                if nDiv == 1 :
                    for i in range(max_len-1):
                        if id != None : id_new = id+i
                        pt_array = [nID_A[i],nID_B[i],nID_B[i+1],nID_A[i+1]]
                        plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id_new))
                if nDiv > 1 :
                    nID_dic = {}
                    for j in range(nDiv+1):
                        nID_dic[j] = []
                    nID_dic[0] = nID_A
                    nID_dic[nDiv] = nID_B
                    for i in range(max_len):
                        loc0= nodeByID(nID_A[i]).LOC
                        loc1 = nodeByID(nID_B[i]).LOC
                        int_points = np.linspace(loc0,loc1,nDiv+1)

                        for j in range(nDiv-1):
                            nID_dic[j+1].append(Node(int_points[j+1][0],int_points[j+1][1],int_points[j+1][2]).ID)
                    j=0
                    for q in range(nDiv):
                        for i in range(max_len-1):
                            if id != None : id_new = id+j
                            pt_array = [nID_dic[q][i],nID_dic[q+1][i],nID_dic[q+1][i+1],nID_dic[q][i+1]]
                            plate_obj.append(Element.Plate(pt_array,stype,mat,sect,angle,group,id_new))
                            j+=1

                return plate_obj

            finalPlateObj = []
            for eID in elmIDs:
                nID_A = []
                nID_B = []
                eObj = elemByID(eID)
                if eObj.TYPE in ('BEAM','TRUSS','TENSTR','COMPTR'):
                    nID_A = eObj.NODE[:2]
                
                    pts_loc = [nodeByID(nID).LOC for nID in nID_A]


                    f_pt = np.add(pts_loc,dir)

                    for i in range(len(nID_A)):
                        nID_B.append(Node(f_pt[i][0],f_pt[i][1],f_pt[i][2]).ID)

                    finalPlateObj+=_createPlateExtrude(nID_A,nID_B,nDiv,id)
                    if id!=None: id+=nDiv

            if bDeleteLine:
                for eID in elmIDs:
                    Element._deleteElem(eID)
  
    class Tension(_common):
     def __init__(self, i: int, j: int, stype: int, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None, non_len: float = None, cable_type: int = None, tens: float = None, t_limit: float = None):

        if id == None: id =0
        self.ID = id
        self.TYPE = 'TENSTR'
        self.MATL = mat
        self.SECT = sect
        self.NODE = [i, j]
        self.ANGLE = angle
        self.STYPE = stype
        self._GROUP = group
        _n1 = nodeByID(i)
        _n2 = nodeByID(j)
        self.CENTER = np.average([_n1.LOC,_n2.LOC],0)
        self.LENGTH = _nodeDIST(_n1,_n2)
        _dirVect = np.subtract(_n2.LOC,_n1.LOC)
        self.LOCALX = np.round(_dirVect/(np.linalg.norm(_dirVect)),4)
        _tempZ = (0.00001,0,1)
        _LOCALY = np.cross(_tempZ,self.LOCALX)
        _ROTLY = _rotatePT(_LOCALY,self.LOCALX,angle)

        self.LOCALY = np.round(_ROTLY / np.linalg.norm(_ROTLY),4)

        _LOCALZ = np.cross(self.LOCALX, self.LOCALY)
        self.LOCALZ = np.round(_LOCALZ / np.linalg.norm(_LOCALZ),4)
        Element.lastLoc = (_n2.X,_n2.Y,_n2.Z)
        
        # Handle subtype-specific parameters
        if stype == 1:  # Tension-only specific
            if tens is not None:
                self.TENS = tens
            if t_limit is not None:
                self.T_LIMIT = t_limit
                self.T_bLMT = True
                
        elif stype == 2:  # Hook specific
            if non_len is not None:
                self.NON_LEN = non_len
                
        elif stype == 3:  # Cable specific
            if cable_type is not None:
                self.CABLE = cable_type
            if non_len is not None:
                self.NON_LEN = non_len
            if tens is not None:
                self.TENS = tens
        _ADD(self)

    class Compression(_common):
        def __init__(self, i: int, j: int, stype: int, mat: int = 1, sect: int = 1, angle: float = 0, group = "" , id: int = None, tens: float = None, t_limit: float = None, non_len: float = None):
           
            if id == None: id =0
            self.ID = id
            self.TYPE = 'COMPTR'
            self.MATL = mat
            self.SECT = sect
            self.NODE = [i, j]
            self.ANGLE = angle
            self.STYPE = stype
            self._GROUP = group
            _n1 = nodeByID(i)
            _n2 = nodeByID(j)
            self.CENTER = np.average([_n1.LOC,_n2.LOC],0)
            self.LENGTH = _nodeDIST(_n1,_n2)
            _dirVect = np.subtract(_n2.LOC,_n1.LOC)
            self.LOCALX = np.round(_dirVect/(np.linalg.norm(_dirVect)),4)
            _tempZ = (0.00001,0,1)
            _LOCALY = np.cross(_tempZ,self.LOCALX)
            _ROTLY = _rotatePT(_LOCALY,self.LOCALX,angle)

            self.LOCALY = np.round(_ROTLY / np.linalg.norm(_ROTLY),4)

            _LOCALZ = np.cross(self.LOCALX, self.LOCALY)
            self.LOCALZ = np.round(_LOCALZ / np.linalg.norm(_LOCALZ),4)
            Element.lastLoc = (_n2.X,_n2.Y,_n2.Z)
            
            # Handle subtype-specific parameters
            if stype == 1:  # Compression-only specific
                if tens is not None:
                    self.TENS = tens
                if t_limit is not None:
                    self.T_LIMIT = t_limit
                    self.T_bLMT = True
                    
            elif stype == 2:  # Gap specific
                if non_len is not None:
                    self.NON_LEN = non_len
            _ADD(self)

    class Solid(_common):
        def __init__(self, nodes: list, mat: int = 1, group = "" , id: int = None):
           
            if id == None: id =0
            if len(nodes) not in [4, 6, 8]:
                raise ValueError("Solid element must have 4, 6, or 8 nodes.")
            self.ID = id
            self.TYPE = 'SOLID'
            self.MATL = mat
            self.SECT = 0 # Solid elements don't use section properties
            _nodesObj = [nodeByID(nId) for nId in nodes]
            _nodesLoc = [node.LOC for node in _nodesObj]
            self.CENTER = np.average(_nodesLoc,0)

            z_Base = np.cross(np.subtract(_nodesObj[1].LOC,_nodesObj[0].LOC),np.subtract(_nodesObj[2].LOC,_nodesObj[1].LOC))

            if len(nodes) == 4:
                # TETRAHEDRAL
                pointTop = np.subtract(_nodesObj[3].LOC,self.CENTER)
                dotP = np.dot(pointTop,z_Base)
                if dotP < 0:
                    # Incorrect direction
                    nodes[:3] = nodes[:3][::-1]
            elif len(nodes) == 6:
                # PRISM
                pointTop = np.subtract(_nodesObj[3].LOC,self.CENTER)
                dotP = np.dot(pointTop,z_Base)
                if dotP < 0:
                    # Incorrect direction
                    nodes = nodes[3:] + nodes[:3]
            elif len(nodes) == 8:
                # HEXA
                pointTop = np.subtract(_nodesObj[4].LOC,self.CENTER)
                dotP = np.dot(pointTop,z_Base)
                if dotP < 0:
                    # Incorrect direction
                    nodes = nodes[4:] + nodes[:4]

            self.NODE = nodes
            

            self._GROUP = group
            _ADD(self)

        @staticmethod
        def extrudeFromPlates(elmIDs,dir=[0,0,1],nDiv = 1, mat=1, group="", id=None, bDeletePlate=False):
            extrusion = [dir[0]/nDiv , dir[1]/nDiv , dir[2]/nDiv]
            id_new = None
            if id!=None: id_new = id-1

            plateElmIDs= [id for id in elmIDs if elemByID(id).TYPE in ['PLATE','WALL']]
            nPlates = len(plateElmIDs)

                    

            for i,eID in enumerate(plateElmIDs):
                eObj = elemByID(eID)
                nID_A = eObj.NODE

                for q in range(nDiv):
                    if id != None : id_new = id_new+1
                    nLOC_A = [nodeByID(pt).LOC for pt in nID_A]

                    nLOC_B = np.add(nLOC_A,extrusion)
                    nID_B = [Node(nLOC_B[i][0],nLOC_B[i][1],nLOC_B[i][2]).ID for i in range(len(nID_A))]

                    _fNIDs = nID_A+nID_B
                    Element.Solid(_fNIDs,mat,group,id_new)

                    nID_A = nID_B
            
            if bDeletePlate:
                for eID in plateElmIDs:
                    Element._deleteElem(eID)

       
# #-----------------------------------------------Stiffness Scale Factor------------------------------

    class StiffnessScaleFactor:
    
        data = []
        
        def __init__(self, 
                    element_id,
                    area_sf: float = 1.0,
                    asy_sf: float = 1.0,
                    asz_sf: float = 1.0,
                    ixx_sf: float = 1.0,
                    iyy_sf: float = 1.0,
                    izz_sf: float = 1.0,
                    wgt_sf: float = 1.0,
                    group: str = "",
                    id: int = None):

            # Check if group exists, create if not
            if group != "":
                chk = 0
                a = [v['NAME'] for v in Group.Boundary.json()["Assign"].values()]
                if group in a:
                    chk = 1
                if chk == 0:
                    Group.Boundary(group)
            
            # Handle element_id as single int or list
            if isinstance(element_id, (list, tuple)):
                self.ELEMENT_IDS = list(element_id)
            else:
                self.ELEMENT_IDS = [element_id]
            
            self.AREA_SF = area_sf
            self.ASY_SF = asy_sf
            self.ASZ_SF = asz_sf
            self.IXX_SF = ixx_sf
            self.IYY_SF = iyy_sf
            self.IZZ_SF = izz_sf
            self.WGT_SF = wgt_sf
            self.GROUP_NAME = group
            
            # Auto-assign ID if not provided
            if id is None:
                self.ID = len(Element.StiffnessScaleFactor.data) + 1
            else:
                self.ID = id
            
            # Add to static list
            Element.StiffnessScaleFactor.data.append(self)
        
        @classmethod
        def json(cls):

            json_data = {"Assign": {}}
            
            for scale_factor in cls.data:
                # Create scale factor item
                scale_factor_item = {
                    "ID": scale_factor.ID,
                    "AREA_SF": scale_factor.AREA_SF,
                    "ASY_SF": scale_factor.ASY_SF,
                    "ASZ_SF": scale_factor.ASZ_SF,
                    "IXX_SF": scale_factor.IXX_SF,
                    "IYY_SF": scale_factor.IYY_SF,
                    "IZZ_SF": scale_factor.IZZ_SF,
                    "WGT_SF": scale_factor.WGT_SF,
                    "GROUP_NAME": scale_factor.GROUP_NAME
                }
                
                # Assign to each element ID
                for element_id in scale_factor.ELEMENT_IDS:
                    if str(element_id) not in json_data["Assign"]:
                        json_data["Assign"][str(element_id)] = {"ITEMS": []}
                    
                    json_data["Assign"][str(element_id)]["ITEMS"].append(scale_factor_item)
            
            return json_data
        
        @classmethod
        def create(cls):

            MidasAPI("PUT", "/db/essf", cls.json())
        
        @classmethod
        def get(cls):

            return MidasAPI("GET", "/db/essf")
        
        @classmethod
        def sync(cls):

            cls.data = []
            response = cls.get()
            
            if response != {'message': ''}:
                processed_ids = set()  # To avoid duplicate processing
                
                for element_data in response.get("ESSF", {}).items():
                    for item in element_data.get("ITEMS", []):
                        scale_factor_id = item.get("ID", 1)
                        
                        # Skip if already processed (for multi-element scale factors)
                        if scale_factor_id in processed_ids:
                            continue
                        
                        # Find all elements with the same scale factor ID
                        element_ids = []
                        for eid, edata in response.get("ESSF", {}).items():
                            for eitem in edata.get("ITEMS", []):
                                if eitem.get("ID") == scale_factor_id:
                                    element_ids.append(int(eid))
                        
                        # Create StiffnessScaleFactor object
                        Element.StiffnessScaleFactor(
                            element_id=element_ids if len(element_ids) > 1 else element_ids[0],
                            area_sf=item.get("AREA_SF", 1.0),
                            asy_sf=item.get("ASY_SF", 1.0),
                            asz_sf=item.get("ASZ_SF", 1.0),
                            ixx_sf=item.get("IXX_SF", 1.0),
                            iyy_sf=item.get("IYY_SF", 1.0),
                            izz_sf=item.get("IZZ_SF", 1.0),
                            wgt_sf=item.get("WGT_SF", 1.0),
                            group=item.get("GROUP_NAME", ""),
                            id=scale_factor_id
                        )
                        
                        processed_ids.add(scale_factor_id)
        
        @classmethod
        def delete(cls):

            cls.data = []
            return MidasAPI("DELETE", "/db/essf")





def elemByID(elemID:int) -> _helperELEM:
    try:
        return (Element.__elemDIC__[str(elemID)])
    except:
        print(f'There is no element with ID {elemID}')
        return None
    
def elemsInGroup(groupName:str,unique:bool=True,reverse:bool=False,output:Literal['ID','ELEM']='ID',order:_order=None) -> list[_helperELEM]:
    groupNames = _convItem2List(groupName)
    elist = []
    for gName in groupNames:
        chk=1
        for i in Group.Structure.Groups:
                if i.NAME == gName:
                    chk=0
                    eIDlist = i.ELIST
                    elist.append(eIDlist)
        if chk:
            print(f'⚠️   "{gName}" - Structure group not found !')
    if unique:
        finalElistID = list(dict.fromkeys(sFlatten(elist)))
    else:
        finalElistID = sFlatten(elist)
  

    if order == None:
        pass
    elif order == 'ID':
        finalElistID.sort()
    else:
        _locationDic = {}
        _a,_b,_c = _location2Index[order]
        for elmID in finalElistID:
            _elmLOC = elemByID(elmID).CENTER
            _locationDic[elmID] = (_elmLOC[_a],_elmLOC[_b],_elmLOC[_c])
        finalElistID = [k for k, v in sorted(_locationDic.items(), key=lambda item: item[1])]

    if reverse: finalElistID = list(reversed(finalElistID))

    if output == 'ELEM':
        finalElistElem = [elemByID(elmID) for elmID in finalElistID]
        return finalElistElem
    
    return finalElistID