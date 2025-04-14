###########################################
# All units to be input as KN, m, Kg, sec #
###########################################


class Fiber:
    def __init__(self, section, material, area, coords):
        self.section = section
        self.material = material
        self.area = area
        self.coords = coords
    
    def generate_fiber_string(self):
        # fiber $yLoc $zLoc $A $matTag
        
        str_fiber = ("fiber " + 
                     str(self.coords[0]) + " "  + 
                     str(self.coords[1]) + " " + 
                     str(self.area) + " " + 
                     str(self.material.id)
                    )
        
        return str_fiber