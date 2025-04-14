###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import material as mat
import fiber as fib
import rebar as reb
import patch as pat
import math as m


class Section:
    def __init__(self, id, type, materials, width, height, patches, rebar_layers, fibers, hoop_scheme):
        self.id = id
        self.type = type
        self.materials = materials
        self.width = width
        self.height = height
        self.area = width * height
        self.i_z = (1/12.0) * width * (height ** 3)
        self.i_y = (1/12.0) * height * (width ** 3)
        
        a = max(self.width, self.height)
        b = min(self.width, self.height)
        
        self.j = a * (b**3) * (1/3.0 - 0.21 * (b/a) * (1 - b**4 / (12.0 * a**4))) # torsion constant (modulus) aka polar moment of inertia --> check: https://roymech.org/Useful_Tables/Torsion.html
        
        v = 0.2 # poisson ratio v = 0.2 for uncracked reinforced concrete -- REFERENCE?????
        self.g_mod = self.materials["unconfined_concrete"].properties["e_mod"] / (2.0 * (1 + v)) # --> Shear modulus -- REFERENCE?????
        
        print("self.g_mod: " + str(self.g_mod))
        print("self.e_mod: " + str(self.materials["unconfined_concrete"].properties["e_mod"]))
        
        self.patches = patches
        self.rebar_layers = rebar_layers
        self.fibers = fibers
        self.hoop_scheme = hoop_scheme # hoops = {"area_bar": value (m2), "separation": value (m)}
    
    
    def generate_fiber_section_string(self):
        str_fiber_section = "\n# " + self.type + '\n'
        str_fiber_section += "section Fiber " + str(self.id) + " -GJ " + str(self.g_mod * self.j) + " {\n"
        
        str_patches = ''
        
        for patch in self.patches:
            str_patches += patch.generate_patch_string() + '\n'
        
        str_rebar_layers = ''
        
        for rebar_layer in self.rebar_layers:
            str_rebar_layers += rebar_layer.generate_rebar_layer_string() + '\n'
        
        str_fibers = ''
        
        for fiber in self.fibers:
            str_fibers += fiber.generate_fiber_string() + '\n'
        
        # final string
        str_fiber_section += (str_patches + '\n' +
                              str_rebar_layers + '\n' + 
                              str_fibers + 
                              '}'
                             )
        
        return str_fiber_section
    
    
    def get_total_long_rebar_area(self):
        
        total_area = 0
        
        for layer in self.rebar_layers:
            total_area += layer.num_bars * layer.area_bar
        
        return total_area


def create_section(section_id, 
                   type, 
                   dimensions, 
                   materials, 
                   patches_scheme, 
                   rebar_scheme, 
                   hoop_scheme, 
                   material_id, 
                   hinge_dist_percentage):
    
    width, height = dimensions
    
    patches = []
    rebar_layers = []
    fibers = []
    
    section = Section(section_id, type, materials, width, height, patches, rebar_layers, fibers, hoop_scheme)
    
    cover = None # we are assuming for the moment that all 4 sides have the same cover (although the scripts are almost ready to implement independent cover depths for each side of the section)
    
    # define rebar layers
    for layer_name in rebar_scheme.keys():
        num_bars, area_bar, cover, location = rebar_scheme[layer_name]
        
        if num_bars == 1 and (location == "RIGHT" or location == "LEFT"):
            coords = [None, 0]
            if location == "RIGHT":
                coords[0] = section.width / 2.0 - cover
            elif location == "LEFT":
                coords[0] = - section.width / 2.0 + cover
            
            # create rebar fiber if required
            fiber = fib.Fiber(section, materials["steel"], area_bar, coords)
            section.fibers.append(fiber)
            
        else:
            rebar_layer = reb.Rebar_Layer(materials["steel"], section, num_bars, area_bar, cover, location)
            section.rebar_layers.append(rebar_layer)
    
    # calculate confined concrete for this section
    if "concrete04" in materials["unconfined_concrete"].type:
        section.materials["confined_concrete"] = mat.create_confined_concrete_material(section, material_id, hinge_dist_percentage)
    else:
        section.materials["confined_concrete"] = materials["unconfined_concrete"]
    
    # define patches
    num_div_y, num_div_z, div_mult = patches_scheme
    
    core_patch = pat.create_core_patch(section, cover, materials["confined_concrete"], num_div_y, num_div_z, div_mult)
    
    (cover_patch_top, 
     cover_patch_bottom, 
     cover_patch_right, 
     cover_patch_left) = pat.create_cover_patches(section, cover, materials["unconfined_concrete"], num_div_y, num_div_z, div_mult)
    
    section.patches.extend([core_patch, cover_patch_top, cover_patch_bottom, cover_patch_right, cover_patch_left])
    
    return section, section.materials["confined_concrete"]


def get_bar_area(diam_mm):
    diam = diam_mm / 1000.0
    area_m2 = m.pi * (diam / 2.0) ** 2
    return round(area_m2, 5)


def create_sections_dict(materials, sections_scheme, hinge_dist_percentage):
    
    material_id = len(materials) + 100 # just to be sure there are no ids collisions
    
    sections = dict()
    confined_concrete_materials = dict()
    
    section_id = 1 # iterates
    
    ################
    # beam section #
    ################
    
    type = "beam"
    beam_dimensions = sections_scheme['beam'] # m
    concrete_material = materials["concrete04_HA175"]
    steel_material = materials["steel02_A400S_non_corrugated"]
    patches_scheme = (4, 6, 3) # (num_div_y, num_div_z, div_mult): div_mult is used to multiply the number of divisions
    
    # rebar_scheme => num_bars, area_bar, cover, location = rebar_scheme[layer_name]
    
    rebar_scheme = {"TOP": (4, get_bar_area(16), 0.03, "TOP"),
                    "MIDDLE": (2, get_bar_area(12), 0.03, "MIDDLE"),
                    "BOTTOM": (5, get_bar_area(16), 0.03, "BOTTOM")
                   }
                   
    hoop_scheme = {"area_bar": get_bar_area(6), "separation": 0.15}
    
    section_materials = {"unconfined_concrete": concrete_material, "steel": steel_material}
    
    beam_section, confined_concrete_beam = create_section(section_id, 
                                                          type, 
                                                          beam_dimensions, 
                                                          section_materials.copy(), 
                                                          patches_scheme, 
                                                          rebar_scheme.copy(), 
                                                          hoop_scheme.copy(),
                                                          material_id,
                                                          hinge_dist_percentage)
                                                         
    confined_concrete_materials[confined_concrete_beam.name] = confined_concrete_beam
    
    material_id += 1
    
    sections["beam"] = beam_section
    
    ###################
    # auxbeam section #
    ###################
    
    section_id += 1
    type = "auxbeam"
    auxbeam_dimensions = sections_scheme['auxbeam'] # m
    concrete_material = materials["concrete04_HA175"]
    steel_material = materials["steel02_A400S_non_corrugated"]
    patches_scheme = (4, 4, 3) # (num_div_y, num_div_z): div_mult is used to multiply the number of divisions
    
    # rebar_scheme => num_bars, area_bar, cover, location = rebar_scheme[layer_name]
    
    rebar_scheme = {"TOP": (3, get_bar_area(12), 0.03, "TOP"),
                    "MIDDLE": (2, get_bar_area(12), 0.03, "MIDDLE"),
                    "BOTTOM": (3, get_bar_area(12), 0.03, "BOTTOM")
                   }
    
    hoop_scheme = {"area_bar": get_bar_area(6), "separation": 0.15}
    
    section_materials = {"unconfined_concrete": concrete_material, "steel": steel_material}
    
    auxbeam_section, confined_concrete_auxbeam = create_section(section_id, 
                                                                type, 
                                                                auxbeam_dimensions, 
                                                                section_materials.copy(), 
                                                                patches_scheme, 
                                                                rebar_scheme.copy(), 
                                                                hoop_scheme.copy(),
                                                                material_id,
                                                                hinge_dist_percentage)
    
    confined_concrete_materials[confined_concrete_auxbeam.name] = confined_concrete_auxbeam
    
    material_id += 1
    
    sections["auxbeam"] = auxbeam_section
    
    ##################
    # column section #
    ##################
    
    section_id += 1
    type = "column"
    column_dimensions = sections_scheme['column'] # m
    concrete_material = materials["concrete04_HA175"]
    steel_material = materials["steel02_A400S_non_corrugated"]
    patches_scheme = (4, 4, 3) # (num_div_y, num_div_z): div_mult is used to multiply the number of divisions
    
    # rebar_scheme => num_bars, area_bar, cover, location = rebar_scheme[layer_name]
    
    # Note that Left and Right rebar layers have only 2 bars because the corner bars are taken by the Top and Bottom layers
    
    rebar_scheme = {"TOP": (4, get_bar_area(16), 0.03, "TOP"),
                    "BOTTOM": (4, get_bar_area(16), 0.03, "BOTTOM"),
                    "LEFT": (2, get_bar_area(16), 0.03, "LEFT"),
                    "RIGHT": (2, get_bar_area(16), 0.03, "RIGHT")
                   }
    
    hoop_scheme = {"area_bar": get_bar_area(6), "separation": 0.15}
    
    section_materials = {"unconfined_concrete": concrete_material, "steel": steel_material}
    
    column_section, confined_concrete_column = create_section(section_id, 
                                                              type,
                                                              column_dimensions,
                                                              section_materials.copy(), 
                                                              patches_scheme, 
                                                              rebar_scheme.copy(), 
                                                              hoop_scheme.copy(), 
                                                              material_id,
                                                              hinge_dist_percentage)
    
    confined_concrete_materials[confined_concrete_column.name] = confined_concrete_column
    
    material_id += 1
    
    sections["column"] = column_section
    
    return sections, confined_concrete_materials
