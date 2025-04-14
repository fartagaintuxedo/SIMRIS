###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import rhinoscriptsyntax as rs
from System.Drawing import Color
import re
import math as m
import processing_importer
import write_tcl_source as w
import functions as f
import material
import section
import element as e
import node as n
import os
import json

# start of building functions

def build_2D_structure(sections, floor_height = 4, max_storeys = 3):
    
    points = rs.GetObjects("select one by one (sequentially) points representing column bases", 1)
    
    rs.EnableRedraw(False)
    
    nodes = []
    elements = []
    
    node_counter, elem_counter = 1, 1
    prev_node = None
    storeys = 1
        
    fixes = [1,1,1, 1,1,1]
    free = [0,0,0, 0,0,0]
    mass = [0,0,0, 0,0,0] # Masses are updated later
    
    while storeys <= max_storeys:
        for i, pt in enumerate(points):
            floor_node = n.Node(node_counter, rs.PointCoordinates(pt), fixes, mass)
            top_node = n.Node(node_counter + len(points), floor_node.coords, free, mass)
            
            node_counter += 1
            
            updated_top_coords = rs.PointAdd(top_node.coords, [0,0,floor_height])
            top_node.coords = updated_top_coords
            
            if storeys == 1:
                nodes.extend([floor_node, top_node])
                floor_node.drawNode()
                top_node.drawNode()
            else:
                nodes.append(top_node)
                top_node.drawNode()
            
            column_elem = e.Element(elem_counter, floor_node, top_node, "column", sections["column"])
            elem_counter += 1
            
            elements.append(column_elem)
            column_elem.drawElement()
            
            #if i == len(points) - 1:
            if i > 0:
                beam_elem = e.Element(elem_counter, prev_top_node, top_node, "beam", sections["beam"])
                elem_counter += 1
                
                elements.append(beam_elem)
                beam_elem.drawElement()
            
            prev_top_node = top_node
            
            
        for i, pt in enumerate(points):
            points[i] = rs.MoveObject(pt, [0, 0, floor_height])
        
        storeys += 1
        
    return nodes, elements


def offset_frames(offset_vector, sections, nodes, elements, total_elements, iter):
    
    new_nodes = dict()
    new_elements = []
    nonbeams = dict()
    
    elem_counter = len(total_elements) + 1
    
    for elem in elements:
        if elem.type != "auxbeam":
            offset_node1 = elem.node1.copy()
            
            offset_node1.id = offset_node1.id + len(nodes)
            
            offset_node1.coords = rs.PointAdd(offset_node1.coords, offset_vector)
            
            offset_node2 = elem.node2.copy()
            
            offset_node2.id = offset_node2.id + len(nodes)
            
            offset_node2.coords = rs.PointAdd(offset_node2.coords, offset_vector)
            
            if str(offset_node1.id) not in new_nodes:
                new_nodes[str(offset_node1.id)] = offset_node1
            
            if str(offset_node2.id) not in new_nodes:
                new_nodes[str(offset_node2.id)] = offset_node2
            
            offset_elem = e.Element(elem_counter, 
                                  offset_node2,
                                  offset_node1,
                                  elem.type,
                                  elem.section)
            
            offset_elem.drawElement()
            elem_counter += 1
            
            new_elements.append(offset_elem)
            
            if elem.type == "beam":
                if (str(elem.node1.id) + str(offset_node1.id)) not in nonbeams:
                    non_bearing_beam1 = e.Element(elem_counter, elem.node1, offset_node1, "auxbeam", sections["auxbeam"])
                    non_bearing_beam1.drawElement()
                    elem_counter += 1
                    new_elements.append(non_bearing_beam1)
                    nonbeams[str(elem.node1.id) + str(offset_node1.id)] = -1
                
                if (str(elem.node2.id) + str(offset_node2.id)) not in nonbeams:
                    non_bearing_beam2 = e.Element(elem_counter, elem.node2, offset_node2, "auxbeam", sections["auxbeam"])
                    non_bearing_beam2.drawElement()
                    elem_counter += 1
                    new_elements.append(non_bearing_beam2)
                    nonbeams[str(elem.node2.id) + str(offset_node2.id)] = -1
        
    new_nodes = new_nodes.values()
    
    for nd in new_nodes:
        nd.drawNode()
    
    return new_nodes, new_elements


def build_3D_structure(sections, max_storeys = 2, floor_height = 4, spans_y = 2, y_dim = 7):
    total_nodes = []
    total_elements = []
    
    nodes, elements = build_2D_structure(sections, floor_height, max_storeys)
    
    print("Total initial nodes: " + str(len(nodes)))
    print("Total initial elements: " + str(len(elements)))
    
    total_nodes.extend(nodes)
    total_elements.extend(elements)
    
    i=1
    
    while i <= spans_y:
        nodes, elements = offset_frames([0, y_dim, 0], sections, nodes, elements, total_elements, i)
        i += 1
        
        print("Total new nodes: " + str(len(nodes)))
        print("Total new elements: " + str(len(elements)))
    
        total_nodes.extend(nodes)
        total_elements.extend(elements)
    
    rs.EnableRedraw(True)
    
    print("Total final nodes: " + str(len(total_nodes)))
    print("Total final elements: " + str(len(total_elements)) + '\n')
        
    return total_nodes, total_elements

# end of building functions

# Viz & layers
rs.AddLayer("columns", Color.DarkGreen)
rs.AddLayer("beams", Color.Red)
rs.AddLayer("auxbeams", Color.Blue)
rs.AddLayer("border_beams", Color.Magenta)
rs.AddLayer("border_auxbeams", Color.Cyan)
rs.AddLayer("text_dots", Color.Gray, visible = False)


# check print
def check_print(node_network_by_levels):
    for k in node_network_by_levels.keys():
        # print("level " + k)
        
        for node_key in node_network_by_levels[k].keys():
            # print("--")
            # print("node " + node_key + " connected to: ")
            
            for elem in node_network_by_levels[k][node_key]:
                print("elem " + str(elem.id) + " of type: " + elem.type)
                
        print("-------------")


def run_building(import_fname, dir, tau_file): 
    
    # dir => 'X' or 'Y'
    
    num_integ_pts = 5
    
    grav_total_steps = 40
    pushover_max_displ = 1.0
    pushover_increm = 0.001
    
    analysis_data = (grav_total_steps, pushover_max_displ, pushover_increm)
    
    hinge_dist_percentage = 10.0 # value in % of hinge length
    
    import_file = open(import_fname)
    import_json_obj = json.load(import_file)
    max_storeys = f.get_storeys(import_json_obj)
    
    sections_scheme = dict()
    
    if max_storeys <= 4:
        sections_scheme['beam'] = (0.3, 0.5)
        sections_scheme['auxbeam'] = (0.3, 0.3)
        sections_scheme['column'] = (0.3, 0.3)
        
    elif max_storeys <= 8:
        sections_scheme['beam'] = (0.36, 0.5)
        sections_scheme['auxbeam'] = (0.36, 0.36)
        sections_scheme['column'] = (0.36, 0.36)
    
    else:
        sections_scheme['beam'] = (0.4, 0.5)
        sections_scheme['auxbeam'] = (0.4, 0.4)
        sections_scheme['column'] = (0.4, 0.4)
    
    
    materials = material.create_materials_dict(hinge_dist_percentage)
    sections, confined_concrete_materials = section.create_sections_dict(materials, sections_scheme, hinge_dist_percentage)
    print(materials)
    
    materials.update(confined_concrete_materials) # extend the dictionary
    print("")
    print(materials)
    
    # max_storeys = 2
    
    # build structure
    # total_nodes, total_elements = build_3D_structure(sections, max_storeys, floor_height = 3, spans_y = 2, y_dim = 4)
    
    building_id = import_fname.split('/')[-1]
    building_id = building_id.split('_structure.json')[0]
    
    print("\nbuilding id: " + building_id + '\n')
    
    draw_struct = False
    if building_id == '7395302TG3379N_137023998' and dir == 'X':
        draw_struct = True
    
    # all elements are imported with their corresponding loads
    nodes_dict, elements_dict = processing_importer.import_structure(import_json_obj, sections, max_storeys, draw_struct)
    
    # get node / elements networks by level (slab)
    node_network_by_levels = f.extract_node_network(elements_dict.values(), nodes_dict.values(), max_storeys)
    
    # calculate diaphragms data and update nodes with their corresponding diaphragm center
    diaphragms, nodes_dict = f.calculate_diaphragms(nodes_dict, node_network_by_levels)
    
    # update nodes with their corresponding masses
    nodes_dict = f.calculate_nodal_masses(nodes_dict, node_network_by_levels)
    
    # write all the data into a .tcl file for opensees
    w.write_opensees_file(materials, 
                          sections, 
                          nodes_dict, 
                          elements_dict, 
                          diaphragms, 
                          dir, 
                          num_integ_pts, 
                          building_id, 
                          analysis_data, 
                          max_storeys,
                          draw_struct)
    
    # only for debugging purposes
    # check_print(node_network_by_levels)
    
    import_file.close()
    
    # write tau factors in a separate file
    tau_factor, equivalent_mass = f.get_sdof_data(diaphragms, nodes_dict)
    tau_file.write(building_id + ",tau_factor:" + str(tau_factor) + ",equivalent_mass:" + str(equivalent_mass) + '\n')



# start of execution

#import_fname = 'building_structure_results/H-type/0605018TG4400N_181160562_structure.json'
#import_fname = 'building_structure_results/C-type/40120A1TG3441S_136983738_structure.json'
#import_fname = 'building_structure_results/T-type/0137003TG4403N_137640836_structure.json'


# list files in directory
base_folder = 'building_structure_results'
folder_names = os.listdir(base_folder)

# setup tau_factor file
tau_file = open("test-bed/bin/results/tau_factors.csv", 'w')

for i,fold_name in enumerate(folder_names):
    file_names = os.listdir(base_folder + '/' + fold_name)
    
    for j,fname in enumerate(file_names):
        if i <30000000000 and j<30000000000:
            dir = 'X' # 'X' or 'Y'
            run_building(base_folder + '/' + fold_name + '/' + fname, dir, tau_file)
            tau_file.flush()
            
            dir = 'Y'
            run_building(base_folder + '/' + fold_name + '/' + fname, dir, tau_file)
            tau_file.flush()
            
tau_file.close()

rs.EnableRedraw(True)



