
import xml.sax
import math
import heapq
import os
import sys

class OSMHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.current_way_nodes = []
        self.current_tag = {}

    def startElement(self, name, attrs):
        if name == 'node':
            id = int(attrs['id'])
            lat = float(attrs['lat'])
            lon = float(attrs['lon'])
            self.nodes[id] = (lat, lon)
        elif name == 'way':
            self.current_way_nodes = []
            self.current_tag = {}
        elif name == 'nd':
            ref = int(attrs['ref'])
            self.current_way_nodes.append(ref)
        elif name == 'tag':
            k = attrs['k']
            v = attrs['v']
            self.current_tag[k] = v

    def endElement(self, name):
        if name == 'way':
            # Filter for streets/roads only
            if 'highway' in self.current_tag:
                # Add edges between consecutive nodes
                for i in range(len(self.current_way_nodes) - 1):
                    u = self.current_way_nodes[i]
                    v = self.current_way_nodes[i+1]
                    
                    if u in self.nodes and v in self.nodes:
                        dist = self.haversine(self.nodes[u], self.nodes[v])
                        
                        if u not in self.edges: self.edges[u] = []
                        if v not in self.edges: self.edges[v] = []
                        
                        self.edges[u].append((v, dist))
                        # Assuming bi-directional for now (unless oneway=yes, but KISS for now)
                        self.edges[v].append((u, dist))

    def haversine(self, coord1, coord2):
        R = 6371  # Earth radius in km
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

class PathFinder:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathFinder, cls).__new__(cls)
            cls._instance.handler = OSMHandler()
            cls._instance.loaded = False
        return cls._instance

    def load_map(self, map_path):
        if self.loaded: return
        print(f"🗺️ Loading map from {map_path}...")
        parser = xml.sax.make_parser()
        parser.setContentHandler(self.handler)
        parser.parse(map_path)
        self.loaded = True
        print(f"✅ Map loaded! Nodes: {len(self.handler.nodes)}, Edges: {len(self.handler.edges)}")

    def find_nearest_node(self, lat, lon):
        min_dist = float('inf')
        nearest_node = None
        # Only iterate over nodes that are actually part of the graph (have edges)
        # This prevents selecting isolated nodes (like POIs, trees) that cause pathfinding to fail.
        for node_id in self.handler.edges:
            if node_id in self.handler.nodes:
                coords = self.handler.nodes[node_id]
                dist = (coords[0] - lat)**2 + (coords[1] - lon)**2
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = node_id
        return nearest_node

    def find_path(self, start_coords, end_coords):
        """
        Dijkstra Algorithm
        start_coords: (lat, lon)
        end_coords: (lat, lon)
        Returns: { 'distance': 'X km', 'time': 'Y min', 'path_nodes': [...] }
        """
        if not self.loaded:
            return {"error": "Map not loaded"}

        start_node = self.find_nearest_node(*start_coords)
        end_node = self.find_nearest_node(*end_coords)

        if not start_node or not end_node:
            return {"error": "Nodes not found"}

        queue = [(0, start_node)]
        distances = {start_node: 0}
        previous = {start_node: None}
        visited = set()

        while queue:
            current_dist, current_node = heapq.heappop(queue)

            if current_node in visited: continue
            visited.add(current_node)

            if current_node == end_node:
                break

            if current_node in self.handler.edges:
                for neighbor, weight in self.handler.edges[current_node]:
                    distance = current_dist + weight
                    if distance < distances.get(neighbor, float('inf')):
                        distances[neighbor] = distance
                        previous[neighbor] = current_node
                        heapq.heappush(queue, (distance, neighbor))

        # Reconstruct path
        path = []
        curr = end_node
        if curr not in previous: 
            return {"distance": "N/A", "time": "N/A", "path": []} # No path found

        while curr is not None:
            path.append(self.handler.nodes[curr])
            curr = previous[curr]
        path.reverse()

        total_km = distances[end_node]
        # Avg speed in city ~30km/h -> 0.5 km/min
        minutes = int(total_km / 30 * 60) 

        return {
            "distance": f"{total_km:.2f} km",
            "time": f"{minutes} min",
            "path": path # List of (lat, lon)
        }
