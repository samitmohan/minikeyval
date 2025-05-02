"""
Consistent Hashing implementation for PyKV
"""
import hashlib


class ConsistentHash:
    """Implementation of consistent hashing for distributing keys"""
    
    def __init__(self, nodes=None, replicas=100):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def add_node(self, node):
        """Add a node to the hash ring"""
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node):
        """Remove a node from the hash ring"""
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            if key in self.ring:
                del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key):
        """Get the node responsible for the given key"""
        if not self.ring:
            return None
            
        hash_key = self._hash(key)
        
        # Find the first point in the ring at or after the hash_key
        for ring_key in self.sorted_keys:
            if ring_key >= hash_key:
                return self.ring[ring_key]
        
        # If we've gone all the way around the ring, return the first node
        return self.ring[self.sorted_keys[0]]
    
    def _hash(self, key):
        """Generate a hash for the given key"""
        return int(hashlib.md5(str(key).encode()).hexdigest(), 16) 