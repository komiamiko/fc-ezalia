"""
Layout generation stage. Consists of:
1. making a set of points where corners can go
2. making a triangulation from those vertices
3. making a graph of the triangles
4. refining the vertex locations
"""
import numpy as np
import numpy.linalg as npl
import numpy.random as npr
import scipy.spatial as spatial
import random

# EZALIA-IMPORT game_info

def make_initial_vertex_map():
  """
  Step 1 of layout - make the initial vertex map.
  
  We do this by generating a set of random points,
  then using repulsive forces to create some distance
  between the points. Uses the Euler method for ODE integration.

  This function returns an array of shape (N, 2)
  which is the (x, y) of each vertex, and an array of
  shape (N,) which is the repulsion factor for each vertex.
  """
  # randomly determine number of vertices
  num_points = random.randint(14, 24) # TODO find good numbers for this
  # put view bounds in a local variable
  boundx, boundy = VIEW_BOUNDS
  # generate initial locations
  pxy = npr.uniform(-1, 1, (num_points, 2))
  pxy *= [[boundx, boundy]]
  # generate random repel factors
  rf = npr.uniform(1, 2, (num_points, 1))
  # simulate like particles
  vxy = np.zeros((num_points, 2), dtype=np.float64)
  sim_iters = 2000
  step_size = 0.25
  vdecay = 0.9 ** step_size
  ref_dist = 600 / num_points
  for _ in range(sim_iters):
    # calculate acceleration for this tick
    axy = np.zeros((num_points, 2), dtype=np.float64)
    # repulsion forces for every pair of vertices
    p1xy = pxy.reshape((num_points, 1, 2))
    p2xy = pxy.reshape((1, num_points, 2))
    dxy = p1xy - p2xy
    ndxy = npl.norm(dxy, axis=2, keepdims=True)
    rfxy = dxy / ndxy ** 3
    rfxy[dxy == 0] = 0 # prevent issues from 0 divided by 0
    rfxy *= rf.reshape((num_points, 1, 1))
    rfxy *= rf.reshape((1, num_points, 1))
    rfxy = np.sum(rfxy, axis=1)
    axy += rfxy * ref_dist ** 2
    # boundary spring-like force
    bxy = np.array([boundx, boundy]).reshape((1, 2))
    bfxy = -bxy - pxy
    bfxy = np.maximum(bfxy, 0)
    axy += bfxy
    bfxy = bxy - pxy
    bfxy = np.minimum(bfxy, 0)
    axy += bfxy
    # decay velocity and apply acceleration
    vxy *= vdecay
    vxy += axy * step_size
    # apply velocity
    pxy += vxy * step_size
  # done simulations
  return pxy

def make_triangulation(vertices):
    """
    Make the Delaunay triangulation for the vertices.
    Does not compute edges and some other useful information.
    
    Returns 3 arrays:
    - triangles as vertex indices, with points in
        counterclockwise order, shape (tris, 3)
    - neighbours as triangle indices, the neighbouring
        triangle opposite to each vertex, shape (tris, 3)
    - edges as vertex indices, with points in counterclockwise order,
        -1 to signal no vertex, shape (verts, max_edges)
    """
    # get stats
    num_points, _ = vertices.shape
    # compute triangulation
    dtri = spatial.Delaunay(vertices)
    tverts = dtri.simplices
    tedges = dtri.neighbors
    # build edge map
    vedges = []
    for iv, it in enumerate(dtri.vertex_to_simplex):
        ive = []
        jt = it
        # roll around
        while True:
            # find index of this vertex
            jtv = np.where(tverts[jt]==iv)[0][0]
            # next triangle over
            kt = tedges[jt][(jtv-1)%3]
            # stop if we're back where we started or reached the outside
            if kt == it or kt == -1:
                break
            # check the next one
            jt = kt
        # roll the other way and record edges as we go
        it = jt
        while True:
            # find index of this vertex
            jtv = np.where(tverts[jt]==iv)[0][0]
            # record an edge
            ive.append(tverts[jt][(jtv+1)%3])
            # next triangle over
            kt = tedges[jt][(jtv+1)%3]
            # stop if we're back where we started or reached the outside
            if kt == it or kt == -1:
                if kt == -1:
                    # not a loop, we also need to record the last edge
                    ive.append(tverts[jt][(jtv-1)%3])
                break
            # check the next one
            jt = kt
        vedges.append(ive)
    # pad all edge arrays to max length
    max_edges = max(map(len, vedges))
    for ive in vedges:
        ive.extend([-1] * (max_edges - len(ive)))
    # convert edge to array
    vedges = np.array(vedges)
    return tverts, tedges, vedges
