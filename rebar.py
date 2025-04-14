###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

class Rebar_Layer:
    def __init__(self, material, section, num_bars, area_bar, cover, location):
        self.material = material
        self.section = section
        self.num_bars = num_bars # IMPORTANT: Left and Right rebar layers must exclude corner rebars from Top and Bottom layers
        self.area_bar = area_bar # all bars in a layer must be of same diameter
        self.cover = cover # lateral covers always same as top / bottom covers assigned
        self.location = location # "TOP", "MIDDLE", "BOTTOM", "RIGHT" or "LEFT"
        self.start_coords, self.end_coords = self.get_coords(self.cover, self.location)
        
    def get_coords(self, cover, location):
        
        start_coords, end_coords = None, None
        
        # Top and Bottom layers span to the corners while Left and Right span in between (to avoid duplicate corner rebars)
        
        if(location == "TOP"):
            start_coords = (-self.section.width / 2.0 + cover, self.section.height / 2.0 - cover)
            end_coords = (self.section.width / 2.0 - cover, self.section.height / 2.0 - cover)
        
        elif(location == "MIDDLE"):
            start_coords = (-self.section.width / 2.0 + cover, 0)
            end_coords = (self.section.width / 2.0 - cover, 0)
            
        elif(location == "BOTTOM"):
            start_coords = (-self.section.width / 2.0 + cover, -self.section.height / 2.0 + cover)
            end_coords = (self.section.width / 2.0 - cover, -self.section.height / 2.0 + cover)
            
        elif(location == "RIGHT"):
            if self.num_bars < 2:
                print("Right rebar layer must have at least 2 bars")
                raise BaseException
            
            y_offset = (self.section.height - 2 * cover) / (self.num_bars + 1)
            
            start_coords = (self.section.width / 2.0 - cover, -self.section.height / 2.0 + cover + y_offset)
            end_coords = (self.section.width / 2.0 - cover, self.section.height / 2.0 - cover - y_offset)
            
        elif(location == "LEFT"):
            if self.num_bars < 2:
                print("Left rebar layer must have at least 2 bars")
                raise BaseException
            
            y_offset = (self.section.height - 2 * cover) / (self.num_bars + 1)
            
            start_coords = (-self.section.width / 2.0 + cover, -self.section.height / 2.0 + cover + y_offset)
            end_coords = (-self.section.width / 2.0 + cover, self.section.height / 2.0 - cover - y_offset)
        
        return (start_coords, end_coords)
    
    def generate_rebar_layer_string(self):
        # layer straight $matTag $numBars $areaBar $yStart $zStart $yEnd $zEnd
        str_rebar_layer = ("layer straight " + 
                           str(self.material.id) + ' ' + 
                           str(self.num_bars) + ' ' + 
                           str(self.area_bar) + ' ' + 
                           str(self.start_coords[0]) + ' ' + 
                           str(self.start_coords[1]) + ' ' + 
                           str(self.end_coords[0]) + ' ' + 
                           str(self.end_coords[1])
                          )
                          
        return str_rebar_layer


