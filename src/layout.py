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

# EZALIA-IMPORT algorithm
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

def make_graph(vertices, tverts, tedges, vedges):
    """
    Make a layout graph from the triangulation.
    Some walls will be open pathways, others will be walls.
    
    Returns 2 arrays:
    - closed edge mask for triangle neighbors
    - closed edge mask for vertex adjacency list
    """
    num_points = vertices.shape[0]
    num_tris = tverts.shape[0]
    # build a set of all edges as (tri, vert, tri, vert)
    #   ______1_
    #  X     /  \_
    #   \  2 |    \_
    #    \   /  0   \_
    #     \ /________ j
    #      3
    # it is guaranteed that E[0] < E[2]
    all_edges = set()
    for it, tri in enumerate(tverts):
        for j in range(3):
            # check that neighbor exists
            jt = tedges[it][j]
            if jt == -1:
                continue
            # ensure it < jt so we don't get repeats
            if jt < it:
                continue
            edge = (it, tri[(j+1)%3], jt, tri[(j-1)%3])
            all_edges.add(edge)
    # now add in the edge length:
    # (length, tri, vert, tri, vert)
    all_edges = [(npl.norm(vertices[edge[3]] - vertices[edge[1]]),) + edge for edge in all_edges]
    # sort, put longest edge first and shortest edge last
    all_edges.sort(reverse=True)
    # add 1 edge at a time, if the regions are not already connected
    tri_uf = UnionFind(num_tris)
    rem_edges = list(all_edges)
    bias_exp = 3 # used to control how much it prefers long edges
    vedges_closed = set()
    while rem_edges:
        edge_index = int(len(rem_edges) * random.uniform(0, 1) ** bias_exp)
        d, t0, v0, t1, v1 = edge = rem_edges.pop(edge_index)
        # edge will be closed if region is already connected
        # edges are open by default, we need to specify when it is closed
        if tri_uf.test_and_join(t0, t1):
            u0, u1 = sorted([v0, v1])
            vedges_closed.add((u0, u1))
    # make the triangle neighbors mask
    tedge_mask = np.zeros(tedges.shape, dtype=bool)
    for it, tri in enumerate(tverts):
        for j in range(3):
            u0, u1 = sorted([tri[(j+1)%3], tri[(j-1)%3]])
            tedge_mask[it][j] = (u0, u1) in vedges_closed
    # make the vertex edge mask
    vedge_mask = np.zeros(vedges.shape, dtype=bool)
    for iv, es in enumerate(vedges):
        for j, jv in enumerate(es):
            if jv == -1:
                continue
            u0, u1 = sorted([iv, jv])
            vedge_mask[iv][j] = (u0, u1) in vedges_closed
    # done
    return tedge_mask, vedge_mask
    
