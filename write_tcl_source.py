###########################################
# All units to be input as KN, m, Kg, sec #
###########################################

import rhinoscriptsyntax as rs
import re
import math as m
import functions as f

def write_nodes(outf, nodes):
    outf.write("\n#nodes coordinates" + '\n')
    
    for nd in nodes:
        coords = ['%.2f' % i for i in nd.coords]
        str_coords = str(coords).replace('\'', '')
        str_coords = str_coords.replace(',', '')
        str_coords = str_coords.replace('[', '')
        str_coords = str_coords.replace(']', '')
        
        outf.write("node " + str(nd.id) + " " + str_coords + '\n')
    
    outf.flush()


def write_diaphragms(outf, diaphragms):
    outf.write("#diaphragms (heads-up: the ids are not sorted by level)")
    
    for diaph in diaphragms.values():
        
        diaph_node_id = diaph["id"]
        diaph_coords = ['%.2f' % i for i in diaph["coords"]]
        x_center, y_center, z_level = [i.replace('\'', '') for i in diaph_coords]
        level_nodes = diaph["nodes"]
        
        outf.write("\nnode " + str(diaph_node_id) + ' ' + str(x_center) + ' ' + str(y_center) + ' ' + str(z_level) + '\n')
        outf.write("\nfix " + str(diaph_node_id) + " 0 0 1" + " 1 1 0" + '\n')
        outf.write("rigidDiaphragm 3 " + str(diaph_node_id) + ' ')
        
        for n in level_nodes:
            outf.write(str(n.id) + ' ')
        outf.write(str('\n'))


def write_boundary_conditions(outf, nodes):
    outf.write("\n#boundary conditions" + '\n')
    
    for nd in nodes:
        str_fixes = str(nd.fixes).replace(',', ' ')
        str_fixes = str(str_fixes).replace('[', '')
        str_fixes = str(str_fixes).replace(']', '')
        outf.write("fix " + str(nd.id) + " " + str_fixes + '\n')
    
    outf.flush()


def write_nodal_masses(outf, nodes):
    outf.write("\n#nodal masses" + '\n')
    
    for nd in nodes:
        node_mass = ['%.2f' % i for i in nd.mass]
        str_mass = str(node_mass).replace('\'', '')
        str_mass = str_mass.replace(',', '')
        str_mass = str_mass.replace('[', '')
        str_mass = str_mass.replace(']', '')
        outf.write("mass " + str(nd.id) + " " + str(str_mass) + '\n')
    
    outf.flush()


def write_geom_transf(outf):
    outf.write("\n#transformation" + '\n')
    
    vecs_xz = [None]*3
    
    vecs_xz[0] = " 0 1 0" #columns
    vecs_xz[1] = " 0 0 1" #beams
    vecs_xz[2] = " 0 0 1" #aux beams
    
    geomTransf_data = {
                       "column" : {"tag_id" : 1, "str_vec" : vecs_xz[0]},
                       "beam" : {"tag_id" : 2, "str_vec" : vecs_xz[1]},
                       "auxbeam" : {"tag_id" : 3, "str_vec" : vecs_xz[2]}
                      }
                       
    transf_type = "Linear"
    
    for k, transf in geomTransf_data.items():
        g_tag = transf["tag_id"]
        str_vec = transf["str_vec"]
        
        outf.write("geomTransf " + transf_type + ' ' + str(g_tag) + str_vec + '\n')
    
    outf.flush()
    
    return geomTransf_data


def write_materials(outf, materials):
    outf.write("\n#materials" + '\n')
    
    for key, mat in materials.items():
        outf.write(mat.material_string + '\n')
    
    outf.flush()


def write_sections(outf, sections):
    outf.write("\n#sections" + '\n')
    
    for key, sec in sections.items():
        print("sec.g_mod: " + str(sec.g_mod))
        print("sec.j: " + str(sec.j))
        str_section = sec.generate_fiber_section_string() + '\n'
        
        outf.write(str_section + '\n')
    
    outf.flush()


# the beamWithHinges element is now obsolete in opensees 3.5.0 - forceBeamColumn should be used instead
def write_beamWithHinges(outf, elements, geomTransf_data):
    # element beamWithHinges $eleTag $iNode $jNode $secTagI $Lpi $secTagJ $Lpj $E $A $Iz $Iy $G $J $transfTag <-mass $massDens> <-iter $maxIters $tol>
    
    outf.write("\n#connectivity" + '\n')
    
    elem_os_type = "beamWithHinges" 
    
    for elem in elements:
        geomTransf_tag = None
        elem_str = None
        
        geomTransf_tag = geomTransf_data[elem.type]["tag_id"]
        
        elem_str = ("element " + elem_os_type + ' ' + 
                    str(elem.id) + ' ' + 
                    str(elem.node1.id) + ' ' +
                    str(elem.node2.id) + ' ' +
                    str(elem.section.id) + ' ' +
                    str(elem.hinge_length) + ' ' +
                    str(elem.section.id) + ' ' +
                    str(elem.hinge_length) + ' ' +
                    str(elem.section.e_mod) + ' ' +
                    str(elem.section.area) + ' ' +
                    str(elem.section.i_z) + ' ' +
                    str(elem.section.i_y) + ' ' +
                    str(elem.section.g_mod) + ' ' +
                    str(elem.section.j) + ' ' +
                    str(geomTransf_tag))
        
        outf.write(elem_str + '\n')
        
    outf.flush()


def write_elements(outf, elements, geomTransf_data, num_integ_pts):
    # element forceBeamColumn $eleTag $iNode $jNode $transfTag $integration <-mass $massDens> <-iter $maxIters $tol>
    
    outf.write("\n#connectivity" + '\n')
    
    elem_model_type = "hinge_integration" # one of: "distributed_plasticity", "hinge_integration" or "regularized_hinge_integration"
    
    for elem in elements:
        elem_str = elem.generate_element_string(geomTransf_data, elem_model_type, num_integ_pts)
        
        outf.write(elem_str + '\n')
        
    outf.flush()


def write_elements2(outf, elements, geomTransf_data, num_integ_pts):
    #element nonlinearBeamColumn $eleTag $iNode $jNode $numIntgrPts $secTag $transfTag
    
    outf.write("\n#connectivity" + '\n')
    
    for elem in elements:
        outf.write("element nonlinearBeamColumn " + 
                   str(elem.id) + ' ' + 
                   str(elem.node1.id) + ' ' + 
                   str(elem.node2.id) + ' ' + 
                   str(num_integ_pts) + ' ' + 
                   str(elem.section.id) + ' ' + 
                   str(geomTransf_data[elem.type]["tag_id"]) + '\n'
                  )
    
    outf.flush()


def write_elements3(outf, elements, geomTransf_data, num_integ_pts):
    #element nonlinearBeamColumn $eleTag $iNode $jNode $numIntgrPts $secTag $transfTag
    
    outf.write("\n#connectivity" + '\n')
    
    for elem in elements:
        outf.write("element elasticBeamColumn " + 
                   str(elem.id) + ' ' + 
                   str(elem.node1.id) + ' ' + 
                   str(elem.node2.id) + ' ' + 
                   str(elem.section.id) + ' ' + 
                   str(geomTransf_data[elem.type]["tag_id"]) + '\n'
                  )
    
    outf.flush()


def write_gravitational_loads(outf, elements):
    outf.write("\n#define load pattern" + '\n')
    
    loadPattern_tag = 1
    ts_type = "Linear"
    
    outf.write("pattern Plain " + str(loadPattern_tag) + ' ' + ts_type + " {" + '\n')
    
    for elem in elements:
        # only create load for elements that have been assigned a load (columns typically are not)
        if elem.uniform_load is not None:
            #careful! order is: Y Z <X> (X is optional) :: as per local coordinates of the element
            str_load = (str(round(elem.uniform_load[1], 2)) + ' ' + 
                        str(round(elem.uniform_load[2], 2))
                        )
            
            # eleLoad -ele 4 5 -type -beamUniform 0.0 -10.0
            outf.write("eleLoad -ele " + str(elem.id) + " -type -beamUniform " + str_load + '\n')
    
    outf.write("}" + '\n')
    outf.flush()


def write_pushover_loads(outf, diaphragms, dir, max_height, draw = False):
    outf.write("\n#define pushover load pattern" + '\n')
    
    loadPattern_tag = 2
    ts_type = "Linear"
    
    outf.write("pattern Plain " + str(loadPattern_tag) + ' ' + ts_type + " {" + '\n')
    
    for diaph in diaphragms.values():
        storey_height = diaph["coords"][2]
        total_weight = 9.81 * sum([node.mass[0] for node in diaph["nodes"]])
        pushover_load = round(total_weight * storey_height / (max_height * 1.00), 2)
        
        str_load = None
        if dir == 'X':
            str_load = str(pushover_load) + " 0.0 0.0" + " 0.0 0.0 0.0"
            
            if draw:
                rs.AddLine(diaph["coords"], [diaph["coords"][0] + pushover_load/10.0, diaph["coords"][1], diaph["coords"][2]])
                
        elif dir == 'Y':
            str_load = "0.0 " + str(pushover_load) + " 0.0" + " 0.0 0.0 0.0"
            
            if draw:
                rs.AddLine(diaph["coords"], [diaph["coords"][0], diaph["coords"][1] + pushover_load/10.0, diaph["coords"][2]])
                
        else:
            print("Fatal error: no valid direction ('X' or 'Y') was passed to the function.")
            raise BaseException
        
        outf.write("load " + str(diaph["id"]) + " " + str_load + '\n')
        
    outf.write("}\n\n")


def write_recorders(outf, building_id, control_node_id, nodes, diaphragms, dir, max_storeys):
    outf.write("#recorders" + '\n')
    
    dof = None
    if dir == 'X':
        dof = 1
    elif dir == 'Y':
        dof = 2
    else:
        print("Fatal error: no valid direction ('X' or 'Y') was passed to the function.")
        raise BaseException
    
    outf.write("recorder Node -file results/displacement/" + 
               building_id + '_' + dir + '_L' + str(max_storeys) + 
               "_control_node.out -time -node " +
               str(control_node_id) + 
               " -dof " + str(dof) + 
               " disp" + 
               '\n\n')
    
    
    diaph_nodes_ids = ''
    
    for diaph in sorted(diaphragms.values(), key=lambda k: k['coords'][2]):
        diaph_nodes_ids += ' ' + diaph['id']
        #print("diaph_node_id " + diaph['id'] + ": " + str(diaph['coords'][2]) + "m")
        
    outf.write("recorder Node -file results/slabs_displacement/" + 
               building_id + '_' + dir + '_L' + str(max_storeys) + 
               "_slabs.out -time -node" +
               str(diaph_nodes_ids) + 
               " -dof " + str(dof) + 
               " disp" + 
               '\n\n')
    
    
    basal_nodes_ids = ''
    
    for n in nodes:
        if n.fixes == [1,1,1, 1,1,1]:
            basal_nodes_ids += ' ' + str(n.id)
            #c = rs.AddCircle(n.coords, .5)
            #rs.ObjectLayer(c, "Layer 05")
    
    # group all ground nodes into a region for easier handling
    outf.write("\n#group all ground nodes into a region for easier handling" + '\n')
    outf.write("region 1 -nodeOnly" + basal_nodes_ids + '\n')
    
    outf.write("recorder Node -file results/shear/" + 
               building_id + '_' + dir + '_L' + str(max_storeys) + 
               "_basal_nodes.out -time -region 1" +
               " -dof " + str(dof) + 
               " reaction" + 
               '\n\n')
    
    outf.flush()
    
    return control_node_id


def write_analysis_settings(outf):
    
    analysis_str = ("#analysis" + '\n' + 
                    "constraints Transformation" + '\n' + 
                    "numberer Plain" + '\n' + 
                    "system BandGeneral" + '\n' + 
                    "test NormDispIncr 1.0e-6 6" + '\n' + 
                    "algorithm Linear" + '\n'
                   )
    
    outf.write(analysis_str)
    
    outf.flush()


def write_gravitational_analysis(outf, dir, control_node_id, total_steps = 40):
    
    increment = 1.0 / (total_steps * 1.00)
    
    analysis_str = (
                    "integrator LoadControl " +
                    str(increment) + '\n' + 
                    "analysis Static" + '\n' + 
                    '\n' + 
                    "analyze " + str(int(total_steps)) + '\n\n' + 
                    "loadConst -time 0.0 \n"
                    )
    
    outf.write(analysis_str)
    
    outf.flush()


def write_pushover_analysis(outf, dir, control_node_id, max_displacement = 1.0, increment = 0.001):
    
    total_steps = max_displacement / increment
    
    dof = None
    if dir == 'X':
        dof = 1
    elif dir == 'Y':
        dof = 2
    else:
        print("Fatal error: no valid direction ('X' or 'Y') was passed to the function.")
        raise BaseException
    
    analysis_str = ("#pushover analysis" + '\n' + 
                    "integrator DisplacementControl " + 
                    str(control_node_id) + ' ' + 
                    str(dof) + ' ' + 
                    str(increment) + '\n' +
                    '\n' + 
                    "analyze " + str(int(total_steps)) + '\n'
                    )
    
    outf.write(analysis_str)
    outf.write("wipe\n") #clear the model and allow opensees writing the output files to disk
    
    outf.flush()


def write_opensees_file(materials, 
                        sections, 
                        nodes_dict, 
                        elements_dict, 
                        diaphragms, 
                        dir, 
                        num_integ_pts, 
                        building_id, 
                        analysis_data, 
                        max_storeys,
                        bool_draw):
    
    grav_total_steps, pushover_max_displ, pushover_increm = analysis_data
    
    nodes = nodes_dict.values()
    elements = elements_dict.values()
    
    #First sort lists by id
    nodes.sort(key=lambda x: x.id, reverse=False)
    elements.sort(key=lambda x: x.id, reverse=False)
    
    outf = open("test-bed/bin/tcl_files/" + building_id + "_" + dir + ".tcl", 'w')
    
    ndm = 3
    ndf = 6
    
    outf.write("model basic -ndm " + str(ndm) + " -ndf " + str(ndf) + '\n')
    
    # Nodes
    write_nodes(outf, nodes)
    
    # Slabs (rigid diaphragms)
    write_diaphragms(outf, diaphragms)
    
    # Boundary conditions
    write_boundary_conditions(outf, nodes)
    
    # Nodal masses
    write_nodal_masses(outf, nodes)
    
    # Geometric transformations
    geomTransf_data = write_geom_transf(outf)
    
    # Materials
    write_materials(outf, materials)
    
    # Sections (i.e. fiber sections)
    write_sections(outf, sections)
    
    # Elements (beamWithHinges) and their connectivity
    write_elements(outf, elements, geomTransf_data, num_integ_pts)
    #write_elements2(outf, elements, geomTransf_data, num_integ_pts)
    #write_elements3(outf, elements, geomTransf_data, num_integ_pts)
    
    # Gravitational loads
    write_gravitational_loads(outf, elements)
    
    # Get the control node
    control_node_id, max_height = f.get_control_node(diaphragms)
    
    # Recorders
    write_recorders(outf, building_id, control_node_id, nodes, diaphragms, dir, max_storeys)
    #write_interstoreyDrift_recorders(outf, building_id, diaphragms, nodes, dir)
    
    # Analysis settings
    write_analysis_settings(outf)
    
    # Gravitational analysis
    write_gravitational_analysis(outf, dir, control_node_id, grav_total_steps)
    
    # Pushover loads
    write_pushover_loads(outf, diaphragms, dir, max_height, bool_draw)
    
    # Pushover analysis
    write_pushover_analysis(outf, dir, control_node_id, pushover_max_displ, pushover_increm)
    
    outf.close()

