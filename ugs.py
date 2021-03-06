import operator, math
import numpy as np
from queue import PriorityQueue
import functools
import os

@functools.lru_cache(maxsize=32768)
def distance(mesh, current, _next):
    # from https://stackoverflow.com/a/1401828
    if current == _next:
        return 0
    return int(np.linalg.norm(mesh.points[current]-mesh.points[_next]))

@functools.lru_cache(maxsize=183646)
def graph_neighbours(mesh, current):
    # Get the points from the cells which have the same point in them
    #print(current)
    #print(mesh.cells['triangle']==current)
    aa= mesh.cells['triangle']==current
    a = np.where(aa)[0]
    b = mesh.cells['triangle'][a]
    points = np.unique(b)
    # remove the current point from these results:
    points = points[points != current]
    
    # Get the elevation of those connected points
    elevations = mesh.point_data['Z'][points]
    # Return a list of connected points, as long as they are above sea-level
    return points[elevations >= 0]
    

def cost_search(mesh, start, travel_cost_function, max_distance=100000):
    frontier = PriorityQueue()  # The priority queue means that we can find the least cost path to continue
    frontier.put(start, 0)      # from, along any path, meaning the resulting paths should always be the least-cost
                                # path to get to that point.
    came_from = {}
    cost_so_far = {}
    dist_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    dist_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        for _next in graph_neighbours(mesh, current):
            # Calculate the cost of going to this new point.
            new_cost = cost_so_far[current] + travel_cost_function(mesh, current, _next)
            # Calculate the eulerian distance to this new point.
            new_dist = dist_so_far[current] + distance(mesh, current, _next)

            # The max_distance check tells the algorithm to stop once we start getting too far away from the starting point.
            if (_next not in cost_so_far or new_cost < cost_so_far[_next]) and new_dist < max_distance:
                cost_so_far[_next] = new_cost
                dist_so_far[_next] = new_dist
                priority = new_cost
                frontier.put(_next, priority)
                came_from[_next] = current

        
    return came_from, cost_so_far

def cost_search(mesh, start, travel_cost_function, max_fuel=1000):
    frontier = PriorityQueue()  # The priority queue means that we can find the least cost path to continue
    frontier.put(start, 0)      # from, along any path, meaning the resulting paths should always be the least-cost
                                # path to get to that point.
    came_from = {}
    cost_so_far = {}
    dist_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    dist_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        for _next in graph_neighbours(mesh, current):
            # Calculate the cost of going to this new point.
            new_cost = cost_so_far[current] + travel_cost_function(mesh, current, _next)
            # Calculate the eulerian distance to this new point.
            new_dist = dist_so_far[current] + distance(mesh, current, _next)

            # The max_distance check tells the algorithm to stop once we start getting too far away from the starting point.
            if (_next not in cost_so_far or new_cost < cost_so_far[_next]) and new_cost <= max_fuel:
                cost_so_far[_next] = new_cost
                dist_so_far[_next] = new_dist
                priority = new_cost
                frontier.put(_next, priority)
                came_from[_next] = current

        
    return came_from, cost_so_far, dist_so_far

"""
from heapq import *
def cost_search(mesh, start, travel_cost_function, max_distance=100000):
    frontier = []                  # The priority queue means that we can find the least cost path to continue
    heappush(frontier, (start, 0)) # from, along any path, meaning the resulting paths should always be the least-cost
                                   # path to get to that point.
    came_from = {}
    cost_so_far = {}
    dist_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    dist_so_far[start] = 0
    while frontier:
        current, priority = heappop(frontier)

        for _next in graph_neighbours(mesh, current):
            # Calculate the cost of going to this new point.
            new_cost = cost_so_far[current] + travel_cost_function(mesh, current, _next)
            # Calculate the eulerian distance to this new point.
            new_dist = dist_so_far[current] + distance(mesh, current, _next)

            # The max_distance check tells the algorithm to stop once we start getting too far away from the starting point.
            if (_next not in cost_so_far or new_cost < cost_so_far[_next]) and new_dist < max_distance:
                cost_so_far[_next] = new_cost
                dist_so_far[_next] = new_dist
                priority = new_cost
                heappush(frontier, (_next, priority))
                came_from[_next] = current


        
    return came_from, cost_so_far
"""

def get_total_cost_for_point(start, mesh, travel_cost_function, max_distance=100000):
    came_from, cost_so_far, dist_so_far = cost_search(mesh, start, travel_cost_function, max_distance)
    
    # Find the edge nodes, and add up their costs to get the total
    total_cost = 0
    for k in came_from.keys():             # For all the points we've visited,
        if k not in came_from.values():    # Find all the points that haven't been 'came_from'
            total_cost += cost_so_far[k]
            
    return total_cost

def get_total_distance_for_all_paths_to_point(start, mesh, travel_cost_function, max_fuel=1000):
    came_from, cost_so_far, dist_so_far = cost_search(mesh, start, travel_cost_function, max_fuel)
    
    # Find the edge nodes, and add up their costs to get the total
    total_dist = 0
    for k in came_from.keys():             # For all the points we've visited,
        if k not in came_from.values():    # Find all the points that haven't been 'came_from'
            total_dist += dist_so_far[k]
            
    return total_dist

def get_from_cell(cell, mesh, travel_cost_function, max_distance=100000):
    start = cell[1]
    return get_from_point(mesh, start, travel_cost_function, max_distance)

def get_dist_from_point(point, mesh, travel_cost_function, max_fuel=1000):
    # Return a tuple of (the point id, it's cost)
    total_dist = get_total_distance_for_all_paths_to_point(point, mesh, travel_cost_function, max_fuel)
    #print(os.getpid(), distance.cache_info())
    return (point, total_dist)

def get_from_point(point, mesh, travel_cost_function, max_distance=100000):
    # Return a tuple of (the point id, it's cost)
    total_cost = get_total_cost_for_point(point, mesh, travel_cost_function, max_distance)
    #print(os.getpid(), distance.cache_info())
    return (point, total_cost)