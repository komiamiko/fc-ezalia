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
  num_points = random.randint(16, 31) # TODO find good numbers for this
  # put view bounds in a local variable
  boundx, boundy = VIEW_BOUNDS
  # generate initial locations
  pxy = npr.uniform(-1, 1, (num_points, 2))
  pxy *= [[boundx, boundy]]
  # generate random repel factors
  rf = npr.uniform(1, 2, (num_points, 1))
  # simulate like particles
  vxy = np.zeros((num_points, 2), dtype=np.float64)
  sim_iters = 100
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
    axy += rfxy
    # boundary spring-like force
    bxy = np.array([boundx, boundy]).reshape((1, 2))
    bfxy = -bxy - pxy
    bfxy = np.maximum(bfxy, 0)
    axy += bfxy
    bfxy = bxy - pxy
    bfxy = np.minimum(bfxy, 0)
    axy += bfxy
    # decay velocity and apply acceleration
    vxy *= 0.9
    vxy += axy
    # apply velocity
    pxy += vxy
  # done simulations
  return pxy
