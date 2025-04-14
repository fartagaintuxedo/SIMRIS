#############################################################################
# CAREFUL! Mander implemmentation --> All strength units to be input as MPa #
# Rest of units as m, Kg, sec                                               #
#############################################################################

# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 17:40:01 2024

@author: jaime
"""

import rhinoscriptsyntax as rs
import math as m


def get_bar_area(diam_mm):
    diam = diam_mm / 1000.0
    area_m2 = m.pi * (diam / 2.0) ** 2
    return area_m2


def get_diam_from_area_bar(area_m2):
    diam = 2 * m.sqrt(area_m2 / m.pi)
    return diam


def calculate_lateral_confining_stress(section):
    # Equations taken from "Theoretical Stress-Strain Model for Confined Concrete" Mander et al 1988
    # https://pdfs.semanticscholar.org/b075/f98187459635da8f57b020cb15db29dbacb3.pdf
    
    # CAREFUL! Mander's equations are in MPa, while the rest of our code is in KPa
    
    # f_1x = ((Asx / (s * dc)) * fyh) * ke
    # f_1y = ((Asy / (s * bc)) * fyh) * ke 
    
    sum_area_long_rebars = 0 # (m2)
    
    for rebar_layer in section.rebar_layers:
        sum_area_long_rebars += rebar_layer.num_bars * rebar_layer.area_bar
    
    s = section.hoop_scheme["separation"] # (m) distance between hoops along the beam / column element
    
    Asx = 2 * section.hoop_scheme["area_bar"] # (m2) total area of transverse reinforcement bar in X direction (we assume 2 bars in each direction)
    Asy = Asx # (m2) we assume same transverse reinforcement in X and Y
    
    # Important! bc must be greater than dc - otherwise values must be swapped
    bc, dc = None, None
    
    cover = section.rebar_layers[0].cover # we are assuming all covers in all layers are the same
    
    if section.height >= section.width:
        bc = section.height - 2 * cover # (m) height of confined (core) area
        dc = section.width - 2 * cover # (m) width of confined (core) area
    else:
        bc = section.width - 2 * cover
        dc = section.height - 2 * cover
        
    fyh = section.materials["steel"].properties["fu"] /1000.0 # 440.0 # (MPa) yield strength of steel (traverse reinforcement) 
    
    ###
    
    rcc = sum_area_long_rebars / (dc * bc) # ratio of longitudinal reinforcement to area of core section
    
    # Attention! these 2 lines below assume there is only 1 long rebar in the middle of the section's height!
    
    w_ = bc / 2.0 # (m) sum of distances between longitudinal bars
    
    sum_w_sq = 2 * ((w_ / 2.0) ** 2)
    
    # Attention! ^^
    
    hoop_diam = get_diam_from_area_bar(section.hoop_scheme["area_bar"])
    
    s_ = s - hoop_diam # (m) interior (diameters excluded) distance between hoops along the element
    
    # ke : confinement effectiveness coefficient
    
    ke = ((1 - sum_w_sq / (6 * bc * dc)) * (1 - s_ / (2 * bc)) * (1 - s_ / (2 * dc))) / (1 - rcc)  
    
    f_1x = ((Asx / (s * dc)) * fyh) * ke # (MPa) lateral confining stress
    
    f_1y = ((Asy / (s * bc)) * fyh) * ke # (MPa) lateral confining stress
    
    f_co = section.materials["unconfined_concrete"].properties["fck"] / 1000.0 # (MPa) unconfined concrte strength -- consider using max strength instead?
    
    f_1x_ratio = f_1x / abs(f_co) # (MPa/MPa)
    f_1y_ratio = f_1y / abs(f_co) # (MPa/MPa)
    
    f_1, f_2 = None, None
    
    # f_2 is always > f_1
    
    if f_1x_ratio >= f_1y_ratio:
        f_1 = f_1y_ratio
        f_2 = f_1x_ratio
    else:
        f_1 = f_1x_ratio
        f_2 = f_1y_ratio
    
    return f_1, f_2


def confined_stress_ratio(section, draw = False):
    
    # f_1 = 0.09
    # f_2 = 0.17
    
    f_1, f_2 = calculate_lateral_confining_stress(section)
    
    print("\nf_1: " + str(f_1) + ", f_2: " + str(f_2) + "\n")
    
    # f_2 is always > f_1
    
    points_ln = []
    points_ln_b = []
    
    top_xaxis_factor = 1 / 10.0 # Do not change this value
    left_yaxis_factor = -14.75 / 0.30 # Adjust only if you know what you are doing
    
    circle_x_center = -15.20
    circle_y_center = -34.63
    
    y0 = left_yaxis_factor * f_1
    r = 42.82
    
    x_int_circle = m.sqrt(r**2 - (y0 - circle_y_center)**2) + circle_x_center
    x0 = x_int_circle
    
    if draw:
        rs.AddPoint([x0, y0, 0])
        rs.AddLine([0, y0, 0], [x0, y0, 0])
    
    for y in range(1,100):
        x = m.log(y) + x0
        
        points_ln.append([x, (-y + 1) + y0, 0])
    
    y_ln_intersect = left_yaxis_factor * f_2
    x_ln_intersect = m.log(-y_ln_intersect + 1 + y0) + x0
    
    if draw:
        rs.AddPoint(x_ln_intersect, y_ln_intersect)
        rs.AddLine([0, y_ln_intersect, 0], [x_ln_intersect, y_ln_intersect, 0])
        rs.AddPolyline(points_ln)
    
    cs_ratio = x_ln_intersect * top_xaxis_factor
    
    print("cs_ratio: " + str(cs_ratio) + "\n")
    
    return cs_ratio


# csr = confined_stress_ratio(section, draw = True)
# print(csr)


#################################################
# concrete deformation at hoop failure (Mander) #
#################################################

# All force related units in MPa and MJ

# calculate concrete deformation at hoop failure

def get_energy_error(ecu, step, section_values):
    
    # 110 * ro_s = area_under(fc) (from 0 to ecu) + ro_cc * area_under(fsl) (from 0 to ecu) - 0.017 * sqrt(f_co)
    
    # Ec --> Young's modulus of concrete
    # Young's modulus of steel
    # eco --> concrete deformation at peak strength (% --> UNE-EN 1992-1-1:2013)
    # f_cc --> strength of confined concrete
    # f_co --> strength of unconfined concrete
    # ro_s --> ratio of transverse steel reinforcement volume to volume of confined concrete core
    # ro_cc --> ratio of longitudinal reinforcement volume to volume of confined concrete core
    
    Ec, E0, eco, ecc, f_cc, f_co, Esec, ro_s, ro_cc = section_values
    
    area_under_fc = 0 
    
    ecc = abs(eco) * (1 + 5 * ((f_cc / f_co) - 1)) # must be positive because f_cc > f_co
    
    # print("ecc: " + str(ecc))
    
    r = Ec / (Ec - Esec)
    
    # fc = f_cc * x * r / (r - 1 + x ** r)
    
    ec = 0
    while ec <= ecu:
        x = ec / ecc
        area_under_fc += (abs(f_cc) * x * r / (r - 1 + x ** r)) * step
        ec += step
    
    
    area_under_fsl = 0
    
    # fsl = E0 * ec # only valid in elastic range (ec < ~0.05)
    
    ec = 0
    while ec <= ecu:
        area_under_fsl += E0 * ec * step
        ec += step
    
    error = area_under_fc + ro_cc * area_under_fsl - 0.017 * m.sqrt(abs(f_co)) - 110 * ro_s 
    return error


def calculate_deformation_hoop_failure(section_values):
    error = 100000
    last_error = 100000000
    
    ecu = 0
    last_ecu = None
    
    step = 0.00001
    iter = 0
    
    # print("error at ecu=0.0035: " + str(get_energy_error(0.0035, step, section_values)))
    
    while abs(error) <= abs(last_error):
        iter += 1
        last_ecu = ecu
        ecu += step
        last_error = error
        error = get_energy_error(ecu, step, section_values)
        # print("error: " + str(error))
    
    print("found ecu: " + str(last_ecu) + ", after " + str(iter) + " iterations, error: " + str(last_error))
    
    # we return last ecu because the current ecu is larger than the last
    return last_ecu
    
    
    









