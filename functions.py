###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import math as m
import rhinoscriptsyntax as rs


def create_nodes_dict(nodes):
    
    nodes_dict = dict()
    
    for n in nodes:
        nodes_dict[str(n.id)] = n
    
    return nodes_dict


def create_elements_dict(elements):
    
    elements_dict = dict()
    
    for e in elements:
        elements_dict[str(e.id)] = e
    
    return elements_dict


def extract_node_network(elements, nodes, levels):
    
    levels_dict = dict()
    
    for elem in elements:
        if elem.type != "column":
            
            # we assume all beams and auxbeams are horizontal
            zcoord = elem.node1.coords[2]
            # maybe it is better to store the level in the element class at time of creation
            level = str(int(zcoord*1000)) # we use mm for indexing
            
            if level not in levels_dict.keys():
                levels_dict[level] = dict()
                levels_dict[level][str(elem.node1.id)] = {elem} # each node has a set of elements that connect to it
                levels_dict[level][str(elem.node2.id)] = {elem}
                
            else:
                if str(elem.node1.id) not in levels_dict[level].keys():
                    levels_dict[level][str(elem.node1.id)] = {elem}
                else:
                    levels_dict[level][str(elem.node1.id)].add(elem)
                    
                if str(elem.node2.id) not in levels_dict[level].keys():
                    levels_dict[level][str(elem.node2.id)] = {elem}
                else:
                    levels_dict[level][str(elem.node2.id)].add(elem)
            
    # now check that we got the right number of levels
    if len(levels_dict.keys()) != levels:
        print("Fatal error: more levels than expected. Raising BaseException now.")
        raise BaseException
    else:
        return levels_dict


# TODO diaphragm ids would be better if sorted by level (not random)
# that might involve ordering first the ids of the node_network_by_levels dict
def calculate_diaphragms(nodes_dict, node_network_by_levels):
    
    diaphragms = dict()
    
    diaph_node_id = len(nodes_dict) # first node id is 1, last is length of list
    
    for k in node_network_by_levels.keys():
        level_nodes = [] # list of node instances associated to the diaphragm
        
        for id in node_network_by_levels[k].keys():
            level_nodes.append(nodes_dict[str(id)])
        
        x_center = sum([n.coords[0] for n in level_nodes])/len(level_nodes)
        y_center = sum([n.coords[1] for n in level_nodes])/len(level_nodes)
        z_level = level_nodes[0].coords[2]
        
        center_coords = [x_center, y_center, z_level]
        
        #rs.AddPoint(x_center, y_center, z_level)
        diaph_node_id += 1
        
        diaphragms[str(diaph_node_id)] = {"id": str(diaph_node_id), "coords": center_coords, "nodes": level_nodes}
        
        for node in level_nodes:
            nodes_dict[str(node.id)].diaphragm_coords = center_coords
    
    return diaphragms, nodes_dict


def calculate_nodal_masses(nodes_dict, node_network_by_levels):
    
    for network_dict in node_network_by_levels.values():
        
        for node_id in network_dict.keys():
            
            node = nodes_dict[node_id]
            # we assume nodes are either completely free or completely fixed
            if 1 in node.fixes:
                # no fixed nodes should show up here, but just in case
                nodes_dict[node_id].mass = [0,0,0, 0,0,0]
                continue
            
            mass = 0
            for elem in network_dict[node_id]:
                
                # we assume loads are only gravitational (vertical) 
                # half the mass of the element goes to the node (should it be 0.6 : 0.4)?
                mass += abs((elem.uniform_load[2]) * 0.5 * elem.length) / 9.81 # divide by gravity to convert from force to mass
            
            delta_x = node.coords[0] - node.diaphragm_coords[0]
            delta_y = node.coords[1] - node.diaphragm_coords[1]
            delta_z = node.coords[2] - node.diaphragm_coords[2] 
            
            # delta z should be zero
            if delta_z != 0:
                print("Fatal error: delta Z not zero. Raising BaseException now.")
                raise BaseException
            
            dist_to_center = m.sqrt(delta_x ** 2 + delta_y ** 2)
            
            mass_momentum = dist_to_center * mass
            nodes_dict[node_id].mass = [mass, mass, 0, 0, 0, mass_momentum]
    
    return nodes_dict


# obsolete: not in use
def get_facade_nodes_by_level(plane_dir_index, nodes_dict, levels):
    # XZ facade: plane_dir_index = 1
    # YZ facade: plane_dir_index = 0
    
    facade_nodes = []
    facade_nodes_by_level = dict()
    
    coords = []
    
    for n in nodes_dict.values():
        coords.append(n.coords[plane_dir_index])
        
    min_val = min(coords)
    
    for n in nodes_dict.values():
        if n.coords[plane_dir_index] == min_val:
            facade_nodes.append(n)
            
            level = str(int(n.coords[2]*1000)) # we use mm for indexing
            
            if level not in facade_nodes_by_level.keys():
                facade_nodes_by_level[level] = [n]
            else:
                facade_nodes_by_level[level].append(n)
    
    return facade_nodes_by_level


# obsolete: not in use
# objects can be either nodes or elements
def get_side_nodes(nodes_list, side):
    # side = 'X' or 'Y'
    xy_key = None
    coord_key1 = None
    coord_key2 = None
    
    if side == 'X':
        xy_key = 0
        coord_key1 = 0
        coord_key2 = 1
        
    elif side == 'Y':
        xy_key = 1
        coord_key1 = 1
        coord_key2 = 0
    else:
        print('Fatal error: unrecognised xy_key. Raising BaseException now.')
        raise BaseException
    
    x_indexing = dict()
    y_indexing = dict()
    
    xy_indexing = (x_indexing, y_indexing)
    
    side_objects = []
    
    for node in nodes_list:
        
        if str(int(node.coords[coord_key1]*1000)) not in xy_indexing[xy_key]:
            xy_indexing[xy_key][str(int(node.coords[coord_key1]*1000))] = dict()
        
        if str(int(node.coords[coord_key2]*1000)) not in xy_indexing[xy_key][str(int(node.coords[coord_key1]*1000))]:
            xy_indexing[xy_key][str(int(node.coords[coord_key1]*1000))][str(int(node.coords[coord_key2]*1000))] = [node]
        else:
            xy_indexing[xy_key][str(int(node.coords[coord_key1]*1000))][str(int(node.coords[coord_key2]*1000))].append(node)
        
    
    print("len(x_indexing)")
    print(len(xy_indexing[0]))
    
    for index in xy_indexing[xy_key].values():
        coord_list = index.keys()
        side_min = min([int(v) for v in coord_list])
        side_max = max([int(v) for v in coord_list])
        
        side_min_objs = index[str(side_min)]
        side_max_objs = index[str(side_max)]
        
        side_objects += side_min_objs
        #side_objects += side_max_objs
        
        for obj in side_min_objs:
            #rs.AddCircle(obj.coords, 0.5)
            pass
        
        for obj in side_max_objs:
            #rs.AddCircle(obj.coords, 0.5)
            pass
    
    return side_objects


def nodes_by_level(node_list, bool_draw):
    
    nodes_by_level = dict()
    
    for node in node_list:
        level = str(int(node.coords[2]*1000)) # we use mm for indexing
            
        if level not in nodes_by_level.keys():
            
            nodes_by_level[level] = [node]
        else:
            nodes_by_level[level].append(node)
    
    #check
    for level_nodes in nodes_by_level.values():
        for node in level_nodes:
            rs.AddCircle(node.coords, node.coords[2]/10.0 + 0.1)
            
    return nodes_by_level


def get_storeys(import_json_obj):
    
    elements = import_json_obj[1]
    
    levels = []
    
    for elem in elements:
        lev = elem["level"]
        levels.append(lev)
        
    max_level = max(levels)
    
    return max_level



def get_control_node(diaphragms):
    # get control node (top diaphragm node)
    top_diaph_node = None
    max_height = 0
    
    for diaph in diaphragms.values():
        storey_height = diaph["coords"][2]
        
        if storey_height > max_height:
            max_height = storey_height
            top_diaph_node = diaph
    
    control_node_id = top_diaph_node["id"]
    
    return control_node_id, max_height



def get_sdof_data(diaphragms, nodes_dict):
    
    # tau_factor = equivalent_mass / eq_mass_denominator
    
    equivalent_mass = 0
    eq_mass_denominator = 0
    
    max_height = max([d["coords"][2] for d in diaphragms.values()])
    
    for diaph in diaphragms.values():
        
        slab_height = diaph["coords"][2]
        
        slab_weight = sum([node.mass[0] for node in diaph["nodes"]]) #X or Y is fine - Z mass is zero
        
        equivalent_mass += slab_weight * (slab_height / max_height)
        
        eq_mass_denominator += slab_weight * ((slab_height / max_height)**2)
    
    
    tau_factor = equivalent_mass / eq_mass_denominator
    
    return tau_factor, equivalent_mass




