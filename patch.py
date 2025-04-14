###########################################
# All units to be input as KN, m, Kg, sec #
###########################################


class Patch:
    #local section coordinates are y,z (y-->horiz, z-->vertical)
    def __init__(self, material, bounds, num_div_y, num_div_z):
        self.material = material
        
        #i,j,k,l points are the 4 corners of the section
        #i-->bottom-left, j-->bottom-right, k-->top-right, l-->top-left
        (self.i_coords, 
         self.j_coords, 
         self.k_coords,
         self.l_coords) = bounds
         
        self.num_div_y = num_div_y
        self.num_div_z = num_div_z
    
    
    def generate_patch_string(self):
        # patch quad $matTag $numSubdivIJ $numSubdivJK $yI $zI $yJ $zJ $yK $zK $yL $zL
        
        str_patch = ("patch quad " + 
                     str(self.material.id) + ' ' +
                     str(self.num_div_y) + ' ' + 
                     str(self.num_div_z) + ' ' + 
                     str(self.i_coords[0]) + ' ' +
                     str(self.i_coords[1]) + ' ' +
                     str(self.j_coords[0]) + ' ' +
                     str(self.j_coords[1]) + ' ' +
                     str(self.k_coords[0]) + ' ' +
                     str(self.k_coords[1]) + ' ' +
                     str(self.l_coords[0]) + ' ' +
                     str(self.l_coords[1])
                    )
        
        return str_patch
    
    
def create_core_patch(section, cover, confined_concrete_material, num_div_y, num_div_z, div_mult):
    
    i_coords = (-section.width/2.0 + cover, -section.height/2.0 + cover)
    j_coords = (section.width/2.0 - cover, -section.height/2.0 + cover)
    k_coords = (section.width/2.0 - cover, section.height/2.0 - cover)
    l_coords = (-section.width/2.0 + cover, section.height/2.0 - cover)
    
    bounds = (i_coords, j_coords, k_coords, l_coords)
    
    core_patch = Patch(confined_concrete_material, bounds, num_div_y * div_mult, num_div_z * div_mult)
    
    return core_patch


def create_cover_patches(section, cover, concrete_material, num_div_y, num_div_z, div_mult):
    
    # TOP patch
    
    i_coords = (-section.width/2.0, section.height/2.0 - cover)
    j_coords = (section.width/2.0, section.height/2.0 - cover)
    k_coords = (section.width/2.0, section.height/2.0)
    l_coords = (-section.width/2.0, section.height/2.0)
    
    bounds_top = (i_coords, j_coords, k_coords, l_coords)
    
    top_patch = Patch(concrete_material, bounds_top, num_div_y * div_mult, 1 * div_mult)
    
    
    # BOTTOM patch
    
    i_coords = (-section.width/2.0, -section.height/2.0)
    j_coords = (section.width/2.0, -section.height/2.0)
    k_coords = (section.width/2.0, -section.height/2.0 + cover)
    l_coords = (-section.width/2.0, -section.height/2.0 + cover)
    
    bounds_bottom = (i_coords, j_coords, k_coords, l_coords)
    
    bottom_patch = Patch(concrete_material, bounds_bottom, num_div_y * div_mult, 1 * div_mult)
    
    
    # RIGHT patch (note we are careful not to overlap at the corners)
    
    i_coords = (section.width/2.0 - cover, -section.height/2.0 + cover)
    j_coords = (section.width/2.0, -section.height/2.0 + cover)
    k_coords = (section.width/2.0, section.height/2.0 - cover)
    l_coords = (section.width/2.0 - cover, section.height/2.0 - cover)
    
    bounds_right = (i_coords, j_coords, k_coords, l_coords)
    
    right_patch = Patch(concrete_material, bounds_right, 1 * div_mult, num_div_z * div_mult)
    
    
    # LEFT patch (note we are careful not to overlap at the corners)
    
    i_coords = (-section.width/2.0 + cover, -section.height/2.0 + cover)
    j_coords = (-section.width/2.0, -section.height/2.0 + cover)
    k_coords = (-section.width/2.0, section.height/2.0 - cover)
    l_coords = (-section.width/2.0 + cover, section.height/2.0 - cover)
    
    bounds_left = (i_coords, j_coords, k_coords, l_coords)
    
    left_patch = Patch(concrete_material, bounds_left, 1 * div_mult, num_div_z * div_mult)
    
    return top_patch, bottom_patch, right_patch, left_patch