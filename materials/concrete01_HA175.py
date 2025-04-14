###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import material as mat
import math as m

# Concrete01 model - Core - Uniaxial Kent-Scott-Park concrete material object with degraded linear unloading/reloading stiffness according to the work of Karsan-Jirsa and no tensile strength

# HA 17.5 (for old RC buildings - before 1980 approx)

def load_material(material_id):
    
    # uniaxialMaterial Concrete01 $matTag $fpc $epsc0 $fpcu $epsU
    
    # $matTag: integer tag identifying material
    # $fpc: concrete compressive strength at 28 days (compression is negative)*
    # $epsc0: concrete strain at maximum strength*
    # $fpcu: concrete crushing strength *
    # $epsU: concrete strain at crushing strength* 
    
    #(Spanish code HA 175 for old RC buildings - before 1980 approx)
    
    fck = -17500.0 # HA 175 (KN/m2) 
    fpc = -24500.0 # HA 175 (KN/m2) --> fck + 8MPa (8000KN/m2) according to EUROCODE (we add only 7 to be safer)
    epsc0 = -0.00193 # (% --> UNE-EN 1992-1-1:2013 --> linear interpolation)
    fpcu = fpc / 10.0 # 10% (estimation based on --> https://link.springer.com/article/10.1007/BF02486177 --> "Strain-softening of concrete in uniaxial compression" - Report of the Round Robin Test carried out by RILEM TC 148-SSC)
    epsU = -0.0035 * 100 / (hinge_dist_percentage * 1.0) # (% --> UNE-EN 1992-1-1:2013)
    # the reason why we multiply ecu by the percentage of hinge length is obscure: 
    # while opensees considers ecu to be a percentage of the total length of the element,
    # only the hinge portion of the element is actually plastifying, 
    # thus, it is better to specify ecu as a percentage of the hinge distance because in reality, 
    # it is as though we were modeling 2 short beams, and this ecu is the ecu value for each of them.
    Ec = 1000 * 8500 * m.pow(abs(fck / 1000.0), 1/3.0) # (KN/m2) initial stiffness (Young's modulus) --> EHE 08 art 39.6
    
    material_string = ("uniaxialMaterial Concrete01 " + 
                       str(material_id)  + ' ' + 
                       str(fck) + ' ' + 
                       str(epsc0) + ' ' + 
                       str(fpcu) + ' ' + 
                       str(epsU)
                      )
    
    concrete01_HA175 = mat.Material(material_id, 
                                    "concrete01_HA175",
                                    "Uniaxial Kent-Scott-Park concrete material object with degraded linear unloading/reloading stiffness according to the work of Karsan-Jirsa and no tensile strength",
                                    "concrete01",
                                    {"fck": fck, "e_mod": Ec, "is_confined": False},
                                    material_string
                                   )
    
    return concrete01_HA175