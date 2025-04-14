###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import sys
sys.path.append(r"materials")
import steel02_A400S_corrugated, steel02_A400S_non_corrugated
import concrete01_HA175, concrete01_HA25, concrete04_HA175, concrete04_HA25
import confined_concrete_calculator as ccc

class Material:
    def __init__(self, id, name, description, type, properties, material_string):
        self.id = id
        self.name = name # "steel_A400S", "concrete_HA25" etc.
        self.description = description # friendly verbose description
        self.type = type # opensees type: "steel02", "concrete04" etc.
        self.properties = properties # {"fck: characteristic strength in KPa, "e_mod": initial stiffness or Young's modulus in KPa, etc}
        self.material_string = material_string # opensees tcl material definition
        
    def clone_material(self, new_id):
        return Material(new_id, 
                        self.name,
                        self.description,
                        self.type,
                        self.properties.copy(),
                        self.material_string)


def create_materials_dict(hinge_dist_percentage):
    
    # Careful! it's important that the ids are consecutive
    # if not adding some materials to the list then their ids should not count
    
    materials = dict()
    mat_id = 1
    
    # mat_steel02_A400S_corrugated = steel02_A400S_corrugated.load_material(str(mat_id))
    # materials[mat_steel02_A400S_corrugated.name] = mat_steel02_A400S_corrugated
    # mat_id += 1
    
    mat_steel02_A400S_non_corrugated = steel02_A400S_non_corrugated.load_material(str(mat_id))
    materials[mat_steel02_A400S_non_corrugated.name] = mat_steel02_A400S_non_corrugated
    mat_id += 1
    
    # mat_concrete01_HA175 = concrete01_HA175.load_material(str(mat_id), hinge_dist_percentage)
    # materials[mat_concrete01_HA175.name] = mat_concrete01_HA175
    # mat_id += 1
    
    # mat_concrete01_HA25 = concrete01_HA25.load_material(str(mat_id), hinge_dist_percentage)
    # materials[mat_concrete01_HA25.name] = mat_concrete01_HA25
    # mat_id += 1
    
    mat_concrete04_HA175 = concrete04_HA175.load_material(str(mat_id), hinge_dist_percentage)
    materials[mat_concrete04_HA175.name] = mat_concrete04_HA175
    mat_id += 1
    
    # mat_concrete04_HA25 = concrete04_HA25.load_material(str(mat_id), hinge_dist_percentage)
    # materials[mat_concrete04_HA25.name] = mat_concrete04_HA25
    
    return materials


def create_confined_concrete_material(section, material_id, hinge_dist_percentage):
    
    unconfined_concrete_material = section.materials["unconfined_concrete"]
    
    new_id = material_id
    
    new_name = "sectionID_" + str(section.id) + "_" + unconfined_concrete_material.name
    
    confined_concrete_material = unconfined_concrete_material.clone_material(new_id)
    
    confined_concrete_material.name = new_name
    
    confined_concrete_material.properties["is_confined"] = True
    
    confined_strength_ratio = ccc.confined_stress_ratio(section, draw = False)
    
    f_co = unconfined_concrete_material.properties["fck"] / 1000.0 # Mander's equations are in MPa
    f_cc = f_co * confined_strength_ratio
    
    confined_concrete_material.properties["fck"] = f_cc * 1000 # Revert to KN 
    
    eco = abs(unconfined_concrete_material.properties["ec"]) # deformation at peak strength for unconfined concrete
    
    ecc = abs(eco) * (1 + 5 * (f_cc / f_co - 1)) # deformation at peak strength for confined concrete -- must be positive because f_cc > f_co
    
    confined_concrete_material.properties["ec"] = -ecc # minus sign to be consistent with criteria
    
    Esec = abs(f_cc / ecc) # Mander (secant E mod)
    print("Esec: " + str(Esec))
    
    Asx = 2 * section.hoop_scheme["area_bar"] # (m2) total area of transverse reinforcement bar in X direction (we assume 2 bars in each direction)
    Asy = Asx # (m2) we assume same transverse reinforcement in X and Y
    
    cover = section.rebar_layers[0].cover # we are assuming all covers in all layers are the same
    
    # here it doesn't matter if dc > bc or vice versa
    bc = section.height - 2 * cover # (m) height of confined (core) area
    dc = section.width - 2 * cover # (m) width of confined (core) area
    
    s = section.hoop_scheme["separation"] # (m) distance between hoops along the beam / column element
    
    ro_s = Asx / (s * dc) + Asy / (s * bc) # ratio of transverse steel reinforcement volume to concrete confined core section volume
    
    ro_cc = section.get_total_long_rebar_area()
    
    Ec = unconfined_concrete_material.properties["e_mod"] / 1000.0 # Mander's equations are in MPa
    E0 = section.materials["steel"].properties["e_mod"] / 1000.0 # Mander's equations are in MPa
    
    print("Ec: " + str(Ec))
    print("E0: " + str(E0))
    
    section_values = Ec, E0, eco, ecc, f_cc, f_co, Esec, ro_s, ro_cc
    
    ecu = ccc.calculate_deformation_hoop_failure(section_values)
    
    confined_concrete_material.properties["ecu"] = -ecu * 100 / (hinge_dist_percentage * 1.0) # minus sign to be consistent with criteria
    # the reason why we multiply ecu by the percentage of hinge length is obscure: 
    # while opensees considers ecu to be a percentage of the total length of the element,
    # only the hinge portion of the element is actually plastifying, 
    # thus, it is better to specify ecu as a percentage of the hinge distance because in reality, 
    # it is as though we were modeling 2 short beams, and this ecu is the ecu value for each of them.
    
    print("base fck: " + str(unconfined_concrete_material.properties["fck"]))
    print("f_cc: " + str(f_cc) + "\n")
    
    if confined_concrete_material.type == "concrete04":
        confined_concrete_material.material_string = rewrite_concrete04_string(confined_concrete_material)
    
    return confined_concrete_material


def rewrite_concrete04_string(confined_concrete_material):
    
    fc = confined_concrete_material.properties["fck"]
    ec = confined_concrete_material.properties["ec"]
    ecu = confined_concrete_material.properties["ecu"]
    Ec = confined_concrete_material.properties["e_mod"]
    
    material_string = ("uniaxialMaterial Concrete04 " + 
                       str(confined_concrete_material.id)  + ' ' + 
                       str(fc) + ' ' + 
                       str(ec) + ' ' + 
                       str(ecu) + ' ' + 
                       str(Ec)
                      )
                      
    return material_string