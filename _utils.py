import numpy as np

def sFlatten(list_of_list):
    # list_of_list = [list_of_list]
    return [item for elem in list_of_list for item in (elem if isinstance(elem, (list,np.ndarray,set,tuple)) else [elem])]

def getID(*objects):
    objects = list(objects)
    _getID2(objects)
    return objects

def _getID2(objects):
    for i in range(len(objects)):
        if isinstance(objects[i], list):
            _getID2(objects[i])  # Recursive call for sublist
        else:
            objects[i] = objects[i].ID

def getLOC(objects):
    ''' Get location for multiple node objects'''
    _getLOC2(objects)
    return objects

def _getLOC2(objects):
    for i in range(len(objects)):
        if isinstance(objects[i], list):
            _getLOC2(objects[i])  # Recursive call for sublist
        else:
            objects[i] = objects[i].LOC

def getNodeID(*objects):
    objects = list(objects)
    _getNodeID2(objects)
    return objects

def _getNodeID2(objects):
    for i in range(len(objects)):
        if isinstance(objects[i], list):
            _getNodeID2(objects[i])  # Recursive call for sublist
        else:
            objects[i] = objects[i].NODE


def arr2csv(nlist):
    strinff = ",".join(map(str,nlist))
    return strinff

def zz_add_to_dict(dictionary, key, value):
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]


def _convItem2List(item):
    if isinstance(item,(list,np.ndarray,tuple)):
        return item
    return [item]

def _matchArray(A,B):
    '''Matches B to length of A   
    Return B'''
    A = _convItem2List(A)
    B = _convItem2List(B)
    n = len(A)
    if len(B) >= n:
        return B[:n]
    return B + [B[-1]] * (n - len(B))

def _longestList(A,B):
    """ Matches A , B list and returns the list with longest length with last element repeated """
    A = _convItem2List(A)
    B = _convItem2List(B)
    nA = len(A)
    nB = len(B)

    if nA >= nB:
        return (A , B + [B[-1]] * (nA - nB))
    return (A + [A[-1]] * (nB - nA),B)