###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import material as mat
import math as m

# Concrete04 model - Core - uniaxial Popovics concrete material object with degraded linear unloading/reloading stiffness according to the work of Karsan-Jirsa and tensile strength with exponential decay

# HA 25 (standard construction concrete)

def load_material(material_id, hinge_dist_percentage):
    
    # uniaxialMaterial Concrete04 $matTag $fc $ec $ecu $Ec
    
    # $matTag: integer tag identifying material
    # $fc: concrete compressive strength at 28 days (compression is negative)*
    # $ec: concrete strain at maximum strength*
    # $ecu: concrete strain at crushing strength* 
    # $Ec: initial stiffness (Young's modulus)
    
    #(Spanish code HA 25 for RC buildings)
    
    fck = -25000.0 # (KN/m2) HA 25
    fc = -32000.0 # (KN/m2) HA 25 --> fck + 8MPa (8000KN/m2) according to EUROCODE (we add only 7 to be safer)
    ec = -0.0021 # (% --> UNE-EN 1992-1-1:2013)
    ecu = -0.0035 * 100 / (hinge_dist_percentage * 1.0) # (% --> UNE-EN 1992-1-1:2013)
    # the reason why we multiply ecu by the percentage of hinge length is obscure: 
    # while opensees considers ecu to be a percentage of the total length of the element,
    # only the hinge portion of the element is actually plastifying, 
    # thus, it is better to specify ecu as a percentage of the hinge distance because in reality, 
    # it is as though we were modeling 2 short beams, and this ecu is the ecu value for each of them.
    Ec = 1000 * 8500 * m.pow(abs(fck / 1000.0), 1/3.0) # (KN/m2) initial stiffness (Young's modulus) --> EHE 08 art 39.6
    
    # For Ec1 see also https://www.codigotecnico.org/pdf/GuiasyOtros/AvanceGuiaCE.pdf page 12
    
    material_string = ("uniaxialMaterial Concrete04 " + 
                       str(material_id)  + ' ' + 
                       str(fck) + ' ' + 
                       str(ec) + ' ' + 
                       str(ecu) + ' ' + 
                       str(Ec)
                      )
    
    properties = {"fck": fck, 
                  "fc": fc, 
                  "ec": ec,
                  "ecu": ecu,
                  "e_mod": Ec, 
                  "is_confined": False
                 }
    
    concrete04_HA25 = mat.Material(material_id, 
                                   "concrete04_HA25",
                                   "uniaxial Popovics concrete material object with degraded linear unloading/reloading stiffness according to the work of Karsan-Jirsa and tensile strength with exponential decay",
                                   "concrete04",
                                   properties,
                                   material_string
                                  )
    
    return concrete04_HA25