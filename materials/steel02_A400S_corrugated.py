###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import material as mat

# steel02 model - uniaxial Giuffre-Menegotto-Pinto steel material object with isotropic strain hardening

# A400S Corrugated Rebar

def load_material(material_id):
    
    # uniaxialMaterial Steel02 $matTag $Fy $E $b $R0 $cR1 $cR2
    
    # $matTag: integer tag identifying material
    # $Fy: yield strength
    # $E0: initial elastic tangent (Young's modulus)
    # $b: strain-hardening ratio (ratio between post-yield tangent and initial elastic tangent)
    # R0, $CR1, $CR2: parameters to control the transition from elastic to plastic branches.

    # Recommended values: $R0=between 10 and 20, $cR1=0.925, $cR2=0.15
    
    fy = 400000.0 # yield strength
    fu = 440000.0 # max strength (--> UNE 36068:2011)
    E0 = 210000000.0 # initial elastic tangent (Young's modulus of steel) (--> UNE EN 10025 & CTE Acero Tabla 4.1)
    eu = 0.05 # strain at max strength (5% --> UNE 36068:2011)
    Ep = (fu - fy) / (eu - fy / E0) # post-yield tangent
    b = Ep / E0 # strain-hardening ratio (ratio between post-yield tangent and initial elastic tangent)
    
    # parameters to control the transition from elastic to plastic branches
    # R0, cR1, cR2 are recommended values -- check paper for updated values -->  "Material Model Parameters for the Giuffre-Menegotto-Pinto Uniaxial Steel Stress-Strain Model"
    
    R0 = 15.0 
    cR1 = 0.925 
    cR2 = 0.15
    
    material_string = ("uniaxialMaterial Steel02 " + 
                       str(material_id)  + ' ' + 
                       str(fy) + ' ' + 
                       str(E0) + ' ' + 
                       str(b) + ' ' + 
                       str(R0) + ' ' + 
                       str(cR1) + ' ' + 
                       str(cR2)
                      )
    
    steel02_A400S_corrugated = mat.Material(material_id,
                                            "steel02_A400S_corrugated",
                                            "uniaxial Giuffre-Menegotto-Pinto steel material object with isotropic strain hardening",
                                            "steel02",
                                            {"fy": fy, "fu": fu, "e_mod": E0},
                                            material_string
                                           )
    
    return steel02_A400S_corrugated
