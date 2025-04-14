###########################################
# All units to be input as KN, m, Kg, sec #
###########################################


import rhinoscriptsyntax as rs

class Element:
    def __init__(self, id, node1, node2, type, section):
        self.id = id
        self.node1 = node1 #object, node 1
        self.node2 = node2 #object, node 2
        self.type = type # "column", "beam" or "auxbeam"
        self.section = section
        self.length = abs(rs.Distance(self.node1.coords, self.node2.coords))
        self.hinge_length = self.length * 10 / 100.0 # 10% of element's length
        self.uniform_load = None # self.assign_load() # uniform load vector
        self.isborder = False
        self.geom_transf = None # TODO --> geometric transform tag should be a property of the element
        
        self.meta = dict() # fill with any properties i.e. isborder = true / false
    
    
    def drawElement(self):
        line = rs.AddLine(self.node1.coords, self.node2.coords)
        dot = rs.AddTextDot(self.id, rs.CurveMidPoint(line))
        rs.ObjectColor(dot, [60,60,200])
    
    
    # temporary function only for testing purposes
    def assign_load(self):
        if self.type == "beam":
            return [0,0,-10]
        elif self.type == "auxbeam":
            return [0,0,-5]
        else:
            return None
    
    
    def generate_element_string(self, geomTransf_data, elem_model_type, num_integ_pts):
        
        # element forceBeamColumn $eleTag $iNode $jNode $transfTag $integration <-mass $massDens> <-iter $maxIters $tol>
        
        elem_os_type = "forceBeamColumn"
        geomTransf_tag = geomTransf_data[self.type]["tag_id"]
        
        elem_str = ("element " + elem_os_type + ' ' + 
                    str(self.id) + ' ' + 
                    str(self.node1.id) + ' ' + 
                    str(self.node2.id) + ' ' + 
                    str(geomTransf_tag) + ' '
                   )
        
        if elem_model_type == "regularized_hinge_integration":
            # read more: https://opensees.berkeley.edu/wiki/images/a/ab/IntegrationTypes.pdf
            # read more: https://sci-hub.st/10.1002/nme.2386
            
            # integration "RegularizedHinge distType nIP secTagI lpI zetaI secTagJ lpJ zetaJ secTagE"
            
            # distType: underlying integration type - Lobatto, Legendre, Radau, or NewtonCotes
            # nIP: number of integration points
            # lpI, lpJ: length of hinges at ends i, j of the element
            # secTagI, secTagJ, secTagE: section Tags (IDs) of the hinges at i, j and in the element's interior
            # zetaI, zetaJ: distance in between additional integration points in the hinges in order to 
            # enforce numerical consistency in the case of strain-hardening response. 
            # Typical values for zetaI and zetaJ range from 0.1% to 1.0% of the element length. 
            
            integration = "RegularizedHinge"
            distType = "Radau" # TODO move to function parameter
            zeta = 1.0 # TODO move to function parameter
            
            elem_str += (integration + ' ' + 
                         str(distType) + ' ' +
                         str(num_integ_pts) + ' ' +
                         str(self.section.id) + ' ' + 
                         str(self.hinge_length) + ' ' + 
                         str(zeta) + ' ' + 
                         str(self.section.id) + ' ' + 
                         str(self.hinge_length) + ' ' + 
                         str(zeta) + ' ' + 
                         str(self.section.id)
                        )
            
            return elem_str
        
        elif elem_model_type == "hinge_integration":
            # note that 4 possible integrations are available for hinged elements 
            # (each comes with a prefixed number of integration points):
            # integration "HingeRadau $secTagI $LpI $secTagJ $LpJ $secTagInterior" 
            # integration "HingeRadauTwo $secTagI $lpI $secTagJ $lpJ $secTagInterior" 
            # integration "HingeMidpoint $secTagI $LpI $secTagJ $LpJ $secTagInterior" 
            # integration "HingeEndpoint $secTagI $lpI $secTagJ $lpJ $secTagInterior" 
            
            integration = "HingeRadau"
            
            elem_str += (integration + ' ' + 
                         str(self.section.id) + ' ' + 
                         str(self.hinge_length) + ' ' + 
                         str(self.section.id) + ' ' + 
                         str(self.hinge_length) + ' ' + 
                         str(self.section.id)
                        )
                        
            
            return elem_str
        
        elif elem_model_type == "distributed_plasticity":
            # possible integration types are:
            # integration "Lobatto $secTag $N" --> Gauss-Lobatto integration is the most common approach for evaluating the response of force-based elements
            # integration "Legendre $secTag $N" --> Gauss-Legendre integration is more accurate than Gauss-Lobatto; however, it is not common in force-based elements because there are no integration points at the element ends
            # integration "Radau $secTag $N" --> Gauss-Radau integration is not common in force-based elements because it places an integration point at only one end of the element; however, it forms the basis for optimal plastic hinge integration methods
            # integration "NewtonCotes $secTag $N" --> Newton-Cotes places integration points uniformly along the element, including a point at each end of the element
            # For more integration options see: https://opensees.berkeley.edu/wiki/images/a/ab/IntegrationTypes.pdf
            
            integration = "Lobatto"
            
            elem_str += (integration + ' ' + 
                         str(self.section.id) + ' ' + 
                         str(num_integ_pts)
                        )
            
            return elem_str