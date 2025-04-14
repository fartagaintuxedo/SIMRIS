###########################################
# All units to be input as KN, m, Kg, sec #
###########################################


import rhinoscriptsyntax as rs

class Node:
    def __init__(self, id, coords, fixes, mass):
        self.id = id
        self.coords = coords
        self.diaphragm_coords = None # center of associated diaphragm
        self.fixes = fixes #vector, constraints on degrees of freedom
        self.mass = mass #vector, one component per degree of freedom
    
    def drawNode(self):
       dot = rs.AddTextDot(self.id, self.coords)
       rs.ObjectColor(dot, [200,60,60])
    
    def copy(self):
        id = self.id
        coords = self.coords
        fixes = self.fixes
        mass = self.mass
        return Node(id, coords, fixes, mass)