import rhinoscriptsyntax as rs
import json
import node as n
import element as e


def import_structure(json_obj, sections, max_level, bool_draw):
    rs.EnableRedraw(False)
    levels_array = []
    
    nodes = json_obj[0]
    elements = json_obj[1]
    
    nodes_dict = dict()
    elements_dict = dict()
    
    gravitational_loads_factor = None 
    infill_factor = None
    mass = [0,0,0, 0,0,0] # masses will be updated later
    
    for nod in nodes:
        if bool_draw:
            rs.AddPoint(nod["coords"])
            d = rs.AddTextDot(nod["id"], nod["coords"])
            rs.ObjectLayer(d, "text_dots")
        
        # self, id, coords, fixes, mass
        node_instance = n.Node(nod["id"], nod["coords"], nod["fixes"], mass)
        nodes_dict[str(nod["id"])] = node_instance
        
    
    for elem in elements:
        node1_id = elem["node_id_1"]
        node2_id = elem["node_id_2"]
        
        level = elem["level"]
        if level == max_level:
            # roof loads
            gravitational_loads_factor = 2
        else:
            # residential floor loads
            gravitational_loads_factor = 8
        
        node1 = nodes_dict[str(node1_id)]
        node2 = nodes_dict[str(node2_id)]
        
        # id, node1, node2, type, section
        elem_instance = e.Element(elem["id"], node1, node2, elem["type"], None)
        
        load_area = elem["load_area"]
        if load_area == None:
            load_area = 0
        
        load_area = round(load_area, 2)
        elem_instance.uniform_load = [0, 0, -load_area * gravitational_loads_factor / elem_instance.length]
        
        if "exterior" in elem["load_area_hint"]:
            elem_instance.isborder = True
            if level == max_level:
                # roof infill loads
                infill_factor = 10.0 / 3.0
            else:
                # residential infill loads
                infill_factor = 10.0
                
            elem_instance.uniform_load[2] -= infill_factor
        
        # assign section from dictionary
        elem_instance.section = sections[elem_instance.type]
        
        elements_dict[str(elem["id"])] = elem_instance
        
        # viz
        if bool_draw:
            l = rs.AddLine(node1.coords, node2.coords)
            if elem_instance.type == "beam":
                rs.ObjectLayer(l, "beams")
                if elem_instance.isborder:
                    rs.ObjectLayer(l, "border_beams")
            elif elem_instance.type == "auxbeam":
                rs.ObjectLayer(l, "auxbeams")
                if elem_instance.isborder:
                    rs.ObjectLayer(l, "border_auxbeams")
            else:
                rs.ObjectLayer(l, "columns")
            
            if elem_instance.uniform_load != None and elem_instance.uniform_load[2] < 0:
                load_line = rs.CopyObject(l, [-0.01 * x for x in elem_instance.uniform_load])
                load_surface = rs.AddSrfPt([elem_instance.node1.coords, 
                                            elem_instance.node2.coords, 
                                            rs.CurvePoints(load_line)[1],
                                            rs.CurvePoints(load_line)[0]])
                                            
                #print("load_line: " + str(load_line))
                #print("load_surface: " + str(load_surface))
                #print("uniform_load: " + str(elem_instance.uniform_load))
                
                if load_surface: 
                    rs.ObjectLayer(load_surface, "Layer 05")
                    rs.SurfaceIsocurveDensity(load_surface, -1)
                    
                rs.DeleteObject(load_line)
    
    if bool_draw: rs.EnableRedraw(True) 
    
    return nodes_dict, elements_dict
