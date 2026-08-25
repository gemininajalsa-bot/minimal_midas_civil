from ._mapi import MidasAPI
from ._utils import zz_add_to_dict,_convItem2List , sFlatten
from math import hypot
from ._group import _add_node_2_stGroup
from typing import Literal
import numpy as np
from ._group import Group

_order = Literal['ID','XYZ','XZY','YXZ','YZX','ZXY','ZYX']


_location2Index = {
    'XYZ' : (0,1,2),
    'XZY' : (0,2,1),
    'YXZ' : (1,0,2),
    'YZX' : (1,2,0),
    'ZXY' : (2,0,1),
    'ZYX' : (2,1,0),
}

def dist_tol(a, b):
    return hypot((a.X-b.X),(a.Y-b.Y),(a.Z-b.Z)) < 0.00001  #TOLERANCE BUILT IN (UNIT INDEP)

def cell(point, size=1):
    return str(f"{int(point.X)},{int(point.Y)},{int(point.Z)}")

# def _cellGrid():
#     [float(x.strip()) for x in list(Node.Grid.keys())split(",")]
# -------- FUNCTIONS ARE DEFINED BELOW TO RECOGNISE NODE CLASS ----------------


class _hNode:
    ID,X,Y,Z,AXIS,LOC = 0,0,0,0,0,0

class Node:
    nodes: list[_hNode] = []
    ids: list[int] = []
    maxID:int = 0
    Grid = {}
    __nodeDic__ = {}

    ## TEMP DATA TO SPEED UP SELECTION FUNCTIONS

    def __init__(self, x: float, y: float, z: float, id: int = None, group: str = '', merge: bool = True):

        if id == None: id =0
        #----------------- ORIGINAL -----------------------
    

        node_count = Node.maxID+1

        # if Node.ids == []: 
        #     node_count = 1
        # else:
        #     node_count = max(Node.ids)+1
        
        
        self.X = float(round(x,6))
        self.Y = float(round(y,6))
        self.Z = float(round(z,6))
        self.AXIS = [[0,0,0],[0,0,0],[0,0,0]]

        if id == 0 : self.ID = node_count
        if id != 0 : self.ID = id

        


        #REPLACE - No merge check
        if id in Node.ids:

            index=Node.ids.index(id)
            n_orig = Node.nodes[index]
            loc_orig = str(cell(n_orig))
            Node.Grid[loc_orig].remove(n_orig)

            loc_new = str(cell(self))
            
            zz_add_to_dict(Node.Grid,loc_new,self)
            Node.nodes[index]=self
            Node.__nodeDic__[str(id)] = self


        #CREATE NEW - Merge Check based on input
        else:
            cell_loc = str(cell(self))      

            if cell_loc in Node.Grid:

                if merge :
                    chk=0   #OPTIONAL
                    for node in Node.Grid[cell_loc]:
                        if dist_tol(self,node):
  
                            chk=1
                            self.ID=node.ID
                            self.AXIS = node.AXIS
                    if chk==0:

                        Node.nodes.append(self)
                        Node.ids.append(self.ID)
                        Node.Grid[cell_loc].append(self)
                        

                else:

                    Node.nodes.append(self)
                    Node.ids.append(self.ID)
                    Node.Grid[cell_loc].append(self)
            else:

                Node.Grid[cell_loc]=[]
                Node.nodes.append(self)
                Node.ids.append(self.ID)
                Node.Grid[cell_loc].append(self)
            Node.__nodeDic__[str(self.ID)] = self
            
        if group !="":
            _add_node_2_stGroup(self.ID,group)

        Node.maxID = max(self.ID,Node.maxID)

    @property
    def LOC(self):
        return (self.X,self.Y,self.Z)

    def __str__(self):
        return f"NODE ID : {self.ID} | X:{self.X} , Y:{self.Y} , Z:{self.Z} \n{self.__dict__}"

    @classmethod
    def json(cls):
        json = {"Assign":{}}
        for i in cls.nodes:
            json["Assign"][i.ID]={"X":i.X,"Y":i.Y,"Z":i.Z}
        return json

    @classmethod
    def create(cls):
        __maxNos__ = 40_000  #40_000 nodes can be sent in a single request
        __numItem__ = len(cls.nodes)
        __nTime__ = int(__numItem__/__maxNos__)+1

        if __nTime__ == 1:
            MidasAPI("PUT","/db/NODE",Node.json())
        else:
            __remainItem__ = __numItem__
            for n in range(__nTime__):
                json = {"Assign":{}}
                __nNode_c__ = min(__maxNos__,__remainItem__)
                for q in range(__nNode_c__):
                    i=cls.nodes[n*__maxNos__+q]
                    json["Assign"][i.ID]={"X":i.X,"Y":i.Y,"Z":i.Z}
                MidasAPI("PUT","/db/NODE",json)
                __remainItem__ -= __maxNos__

        
    @staticmethod
    def get():
        return MidasAPI("GET","/db/NODE")

    @staticmethod
    def sync():
        Node.clear()
        a = Node.get()
        if a != {'message': ''}:
            if list(a['NODE'].keys()) != []:
                for j in a['NODE'].keys():
                    Node(round(a['NODE'][j]['X'],6), round(a['NODE'][j]['Y'],6), round(a['NODE'][j]['Z'],6), id=int(j), group='', merge=False)

    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/NODE")
        Node.clear()

    @staticmethod
    def clear():
        Node.nodes=[]
        Node.ids=[]
        Node.Grid={}
        Node.__nodeDic__ = {}
        Node.maxID = 0

    @staticmethod
    def SE(s_loc: list, e_loc: list, n: int = 1, id: int = None, group: str = '', merge: bool = True):
        id_new = None
        if isinstance(s_loc,Node):
            s_loc = (s_loc.X,s_loc.Y,s_loc.Z)
        if isinstance(e_loc,Node):
            e_loc = (e_loc.X,e_loc.Y,e_loc.Z)

        beam_nodes =[]
        i_loc = np.linspace(s_loc,e_loc,n+1)
        for i in range(n+1):
            if id != None : id_new = id+i
            beam_nodes.append(Node(i_loc[i][0].item(),i_loc[i][1].item(),i_loc[i][2].item(),id_new,group,merge))

        return beam_nodes

    @staticmethod
    def SDL(s_loc: list, dir: list, l: float, n: int = 1, id: int = None, group: str = '', merge: bool = True):
        if isinstance(s_loc,Node):
            s_loc = (s_loc.X,s_loc.Y,s_loc.Z)

        beam_nodes =[]
        s_locc = np.array(s_loc)
        unit_vec = np.array(dir)/np.linalg.norm(dir)

        for i in range(n+1):
            if id != None : id_new = id+i
            else: id_new = None
            locc = s_locc+i*l*unit_vec/n
            beam_nodes.append(Node(locc[0].item(),locc[1].item(),locc[2].item(),id_new,group,merge))

        return beam_nodes

    @staticmethod
    def fromList(nodesList: list, id: int = None, group: str = '', merge: bool = True):
        beam_nodes=[]
        for i,pt in enumerate(nodesList):
            if id != None : id_new = id+i
            else: id_new = None
            beam_nodes.append(Node(pt[0],pt[1],pt[2],id_new,group,merge))

        return beam_nodes
    




def nodesInGroup(groupName: str, unique: bool = True, reverse: bool = False, output: Literal['ID','NODE'] = 'ID',order:_order=None) -> list[_hNode]:
    groupNames = _convItem2List(groupName)
    nlist = []
    for gName in groupNames:
        chk=1
        for i in Group.Structure.Groups:
                if i.NAME == gName:
                    chk=0
                    eIDlist = i.NLIST
                    nlist.append(eIDlist)
        if chk:
            print(f'⚠️   "{gName}" - Structure group not found !')
    if unique:
        finalNlistID = list(dict.fromkeys(sFlatten(nlist)))
    else:
        finalNlistID = sFlatten(nlist)
  

    if order == None:
        pass
    elif order == 'ID':
        finalNlistID.sort()
    else:
        _locationDic = {}
        _a,_b,_c = _location2Index[order]
        for nID in finalNlistID:
            _nLOC = nodeByID(nID).LOC
            _locationDic[nID] = (_nLOC[_a],_nLOC[_b],_nLOC[_c])
        finalNlistID = [k for k, v in sorted(_locationDic.items(), key=lambda item: item[1])]

    if reverse: finalNlistID = list(reversed(finalNlistID))

    if output == 'NODE':
        finalNlistNode = [nodeByID(nID) for nID in finalNlistID]
        return finalNlistNode
    
    return finalNlistID

def nodeByID(nodeID: int) -> Node:
    try:
        return (Node.__nodeDic__[str(nodeID)])
    except:
        print(f'There is no node with ID {nodeID}')
        return None

def closestNode(point_location) -> Node:
    gridStr = list(Node.Grid.keys())
    gridInt = []
    for key in gridStr:
        gridInt.append([int(x) for x in key.split(",")])

    bNode = False
    bNodeID = 0
    if isinstance(point_location,int):
        bNode = True
        bNodeID = point_location
        nodeP = nodeByID(point_location)
        point_location = (nodeP.X,nodeP.Y,nodeP.Z)
    elif isinstance(point_location,Node):
        bNode = True
        bNodeID = point_location.ID
        point_location = (point_location.X,point_location.Y,point_location.Z)
    pGridInt = [int(point_location[0]),int(point_location[1]),int(point_location[2])]
    pGridStr = f"{int(point_location[0])},{int(point_location[1])},{int(point_location[2])}"

    min_edge_dist = round(min(point_location[0]-pGridInt[0],point_location[1]-pGridInt[1],point_location[2]-pGridInt[2]),3)
    max_edge_dist = round(max(point_location[0]-pGridInt[0],point_location[1]-pGridInt[1],point_location[2]-pGridInt[2]),3)

    if min_edge_dist > 0.5 : min_edge_dist = round(1-min_edge_dist,3)
    if max_edge_dist > 0.5 : max_edge_dist = round(1-max_edge_dist,3)

    min_edge_dist = min(min_edge_dist,max_edge_dist)

    min_dist = 10000000000  #Large value for initial value
    min_node = 0
    checked_GridInt = []

    if bNode and len(Node.Grid[pGridStr]) == 1:
        gridDist = []
        for gInt in gridInt:
            gridDist.append(abs(gInt[0]-pGridInt[0])+abs(gInt[1]-pGridInt[1])+abs(gInt[2]-pGridInt[2]))
        gridDistSort = sorted(gridDist)

        nearestGridIdx = gridDist.index(gridDistSort[1])
        nearestGridInt = gridInt[nearestGridIdx]
        nearestGridStr = gridStr[nearestGridIdx]
    else:
        if pGridInt in gridInt :
            nearestGridInt = pGridInt
            nearestGridStr = pGridStr
        else :
            gridDist = []
            for gInt in gridInt:
                gridDist.append(abs(gInt[0]-pGridInt[0])+abs(gInt[1]-pGridInt[1])+abs(gInt[2]-pGridInt[2]))

            nearestGridIdx = gridDist.index(min(gridDist))
            nearestGridInt = gridInt[nearestGridIdx]
            nearestGridStr = gridStr[nearestGridIdx]

    for nd in Node.Grid[nearestGridStr]:
        dist = hypot(nd.X-point_location[0],nd.Y-point_location[1],nd.Z-point_location[2])
        if dist < min_dist and nd.ID !=bNodeID:
            min_dist = dist
            min_node = nd
    checked_GridInt.append(nearestGridInt)
    if min_dist < min_edge_dist :
        return min_node
    
    else:
        # COMBINATION POSSIBLE FOR CELLS
        minX = int(point_location[0]-min_dist)
        maxX = int(point_location[0]+min_dist)
        minY = int(point_location[1]-min_dist)
        maxY = int(point_location[1]+min_dist)
        minZ = int(point_location[2]-min_dist)
        maxZ = int(point_location[2]+min_dist)
        possible = maxX+maxY+maxZ-minX-minY-minZ
        if possible == 0:
            return min_node

        for i in np.arange(minX,maxX+1,1):
            for j in np.arange(minY,maxY+1,1):
                for k in np.arange(minZ,maxZ+1,1):
                    cgridStr = f"{i},{j},{k}"
                    cgridInt = [i,j,k]

                    if cgridInt in checked_GridInt:
                        continue
                    else:
                        if cgridInt in gridInt:
                            for nd in Node.Grid[cgridStr]:
                                dist = hypot(nd.X-point_location[0],nd.Y-point_location[1],nd.Z-point_location[2])
                                if dist < min_dist and nd.ID !=bNodeID:
                                    min_dist = dist
                                    min_node = nd
                        checked_GridInt.append(cgridInt)
        return min_node

def _ifNodeExist_(x, y, z) -> tuple:
    cell_loc = str(f"{int(x)},{int(y)},{int(z)}")
    if cell_loc in Node.Grid:
        for node in Node.Grid[cell_loc]:
            if hypot((x-node.X),(y-node.Y),(z-node.Z)) < 0.00001 :
                return True,node.ID
    return False,0


def nodesInRadius(point_location, radius: float = 0, output: Literal['ID','NODE'] = 'ID', includeSelf: bool = False , bDistOutput=False) -> list:
    gridStr = list(Node.Grid.keys())

    bNode = False
    id2Remove = 0
    if isinstance(point_location,int):
        bNode = True
        id2Remove = point_location
        nodeP = nodeByID(point_location)
        point_location = (nodeP.X,nodeP.Y,nodeP.Z)
        
    elif isinstance(point_location,Node):
        bNode = True
        id2Remove = point_location.ID
        point_location = (point_location.X,point_location.Y,point_location.Z)

    if not includeSelf and not bNode:
        bNode,id2Remove = _ifNodeExist_(point_location[0],point_location[1],point_location[2])

    ifRemove = bNode and not includeSelf

    checked_GridStr = []
    close_nodes:list[int] = []
    close_nodesID:list[Node] = []
    _dist_record = {}


    minX = int(point_location[0]-radius)
    maxX = int(point_location[0]+radius)
    minY = int(point_location[1]-radius)
    maxY = int(point_location[1]+radius)
    minZ = int(point_location[2]-radius)
    maxZ = int(point_location[2]+radius)

    gridStr = set(Node.Grid.keys())
    grid_complete = Node.Grid

    from ._model import _returnCommonGrid_
    common_gridStr = _returnCommonGrid_(gridStr,minX,maxX,minY,maxY,minZ,maxZ)

    for eachAvailGrid in common_gridStr:
        for nd in grid_complete[eachAvailGrid]:
            dist = hypot(nd.X-point_location[0],nd.Y-point_location[1],nd.Z-point_location[2])
            if dist <= radius+0.0001 :
                close_nodes.append(nd)
                close_nodesID.append(nd.ID)
                _dist_record[nd.ID] = dist

    if output == 'NODE':
        if ifRemove:
            close_nodes.remove(nodeByID(id2Remove))
            if bDistOutput:
                return [(node,_dist_record[node.ID]) for node in close_nodes]
            else:
                return close_nodes
    if ifRemove:
        close_nodesID.remove(id2Remove)
    
    if bDistOutput:
        return [(nID,_dist_record[nID]) for nID in close_nodesID]
    else:
        return close_nodesID



class NodeLocalAxis:

    skew = []
    ids = []

    def __init__(self, nodeID: int, type: Literal['X', 'Y', 'Z', 'XYZ', 'Vector'], angle):

        self.ID = nodeID

        if nodeID in NodeLocalAxis.ids:
            index = NodeLocalAxis.ids.index(nodeID)
            intial_angle = NodeLocalAxis.skew[index].ANGLE
            if intial_angle == [[0,0,0],[0,0,0],[0,0,0]]:
                intial_angle = [[1,0,0],[0,1,0],[0,0,1]]

            if type == 'Vector':
                self.TYPE = 'VEC'
                self.VEC = angle
            elif type == 'X':
                self.TYPE = 'ANGLE'
                self.ANGLE = [angle,intial_angle[1],intial_angle[2]]
            elif type == 'Y':
                self.TYPE = 'ANGLE'
                self.ANGLE = [intial_angle[0],angle,intial_angle[2]]
            elif type == 'Z':
                self.TYPE = 'ANGLE'
                self.ANGLE = [intial_angle[0],intial_angle[1],angle]
            elif type == 'XYZ':
                self.TYPE = 'ANGLE'
                self.ANGLE = angle
            NodeLocalAxis.skew[index] = self
        else:
            if type == 'Vector':
                self.TYPE = 'VEC'
                self.VEC = angle
                self.ANGLE = [0,0,0]
            elif type == 'X':
                self.TYPE = 'ANGLE'
                self.ANGLE = [angle,0,0]
            elif type == 'Y':
                self.TYPE = 'ANGLE'
                self.ANGLE = [0,angle,0]
            elif type == 'Z':
                self.TYPE = 'ANGLE'
                self.ANGLE = [0,0,angle]
            elif type == 'XYZ':
                self.TYPE = 'ANGLE'
                self.ANGLE = angle
        
            NodeLocalAxis.skew.append(self)
            NodeLocalAxis.ids.append(self.ID)

    @classmethod
    def json(cls):
        json = {"Assign":{}}
        for i in cls.skew:
            if i.TYPE == 'ANGLE':
                json["Assign"][i.ID]={
                                    "iMETHOD": 1,
                                    "ANGLE_X": i.ANGLE[0],
                                    "ANGLE_Y": i.ANGLE[1],
                                    "ANGLE_Z": i.ANGLE[2]
                                }
            elif i.TYPE == 'VEC':
                json["Assign"][i.ID]={
                                    "iMETHOD": 3,
                                    "V1X": i.VEC[0][0],
                                    "V1Y": i.VEC[0][1],
                                    "V1Z": i.VEC[0][2],
                                    "V2X": i.VEC[1][0],
                                    "V2Y": i.VEC[1][1],
                                    "V2Z": i.VEC[1][2]
                                }
        return json

    @staticmethod
    def create():
        MidasAPI("PUT","/db/SKEW",NodeLocalAxis.json())

    @staticmethod
    def delete():
        MidasAPI("DELETE","/db/SKEW")
        NodeLocalAxis.clear()

    @staticmethod
    def clear():
        NodeLocalAxis.skew=[]
        NodeLocalAxis.ids=[]

    @staticmethod
    def get():
        return MidasAPI("GET","/db/SKEW")
    