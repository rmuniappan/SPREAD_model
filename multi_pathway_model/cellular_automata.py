class Cell(object):
    """
    Object for cell of cellular automata.
    """
    def __init__(self, ID=None, temperature=None, ndvi=None, 
                 humidity=None, production=None, country = None, population = None, time=None, 
                 vertices=None, neighbors=None,
                 weights=None):
        self._ID = ID
        self._temperature = []
        self._ndvi = []
        self._humidity = []
        self._production = {}
	self._country = ''
	self._population = 0
        self._time= time   # time of infection
        # Vertices is a list of points that form the polygon of the cell and the
        # last point is the centroid. Note: the cell does not have to be a
        # rectangle.
        self._vertices = vertices
        self._neighbors = neighbors # a list of neighbor node id.
        self._predecessors = list()
        self._weights = weights # a dict {neighbor_id:[short_distance, voronoi, distance_without, distance]}
        self._state = 'S'
        
    # APIs
    @property
    def ID(self):
        return self._ID

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, t):
        self._temperature = t

    @property
    def ndvi(self):
        return self._ndvi

    @ndvi.setter
    def ndvi(self, ndvi):
        self._ndvi = ndvi

    @property
    def humidity(self):
        return self._humidity

    @humidity.setter
    def humidity(self, h):
        self._humidity = h

    @property
    def production(self):
        return self._production

    @production.setter
    def production(self, p):
        self._production = p

    @property
    def country(self):
	return self._country

    @country.setter
    def country(self, c):
	self._country = c

    @property
    def population(self):
	return self._population

    @population.setter
    def population(self, p):
	self._population = p

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, t):
        self._time = t

    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, v):
        self._vertices = v

    @property
    def neighbors(self):
        return self._neighbors

    @neighbors.setter
    def neighbors(self, n):
        self._neigbhors = n

    @property
    def predecessors(self):
        return self._predecessors

    @predecessors.setter
    def predecessors(self, p):
        self._predecessors = p

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, w):
        self._weights = w
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, s):
        self._state = s

class CA(object):
    def __init__(self, time=None, cells=None):
        self._time = time
        self._cells = cells
        self._ids = list()
        self._cell_dict = dict()
        self._initializing()

    #APIs
    @property
    def time(self):
        return self._time

    @property
    def cells(self):
        return self._cells

    @cells.setter
    def cells(self, c):
        self._cells=c

    @property
    def ids(self):
        return self._ids

    @ids.setter
    def ids(self, IDs):
        self._ids = IDs

    @property
    def cell_dict(self):
        return self._cell_dict

    @cell_dict.setter
    def cell_dict(self, d):
        self.cell_dict = d

    def add_cell(self, cell):
        self._cells.append(cell)
        
    def get_cell(self, ID):
        return self._cell_dict[ID]

    def add_edge(self, s, e, edge_type, weight, reverse=False):
        """
        Add an edge s->e, if reverse set true, an edge e->s will also be
        added.
        """
        source = self._cell_dict[s]
        end = self._cell_dict[e]
        if e not in source.neighbors:    
            source.neighbors.append(e)
            source.weights[e] = [-1, -1, -1, -1]
        
        if s not in end.predecessors:
            end.predecessors.append(s)

        if edge_type=='sd':
            source.weights[e][0] = weight
        elif edge_type=='voronoi':
            if source.weights[e][1] != -1: # if an edge is exsiting, add flow to it
                source.weights[e][1] += weight
            else:
                source.weights[e][1] = weight
        elif edge_type=='distance_without':
            if source.weights[e][2] != -1:
                source.weights[e][2] += weight
            else:
                source.weights[e][2] = weight
	elif edge_type=='distance':
            if source.weights[e][3] != -1:
                source.weights[e][3] += weight
            else:
                source.weights[e][3] = weight

        if reverse==True:
            add_edge(self, e, s, edge_type, weight, reverse=False) 

    # internal functions
    def _initializing(self):
        for cell in self._cells: # set id to cell map
            self.ids.append(cell)
            self.cell_dict[cell] = self._cells[cell]

        for cell in self._cells: # set predecessor list for each successor
                
		for nb in self._cells[cell].neighbors:
                    neighbor = self.cell_dict[nb[0]]    #JM: the nb[0] is to account for the neighbor now being a tuple
                    if cell not in neighbor.predecessors:
                        neighbor.predecessors.append(cell)
                



