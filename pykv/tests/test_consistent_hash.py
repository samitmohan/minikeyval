"""
Tests for the ConsistentHash implementation
"""
import unittest
from pykv.common.consistent_hash import ConsistentHash


class TestConsistentHash(unittest.TestCase):
    """Test cases for ConsistentHash class"""
    
    def test_initialization(self):
        """Test that ConsistentHash initializes properly"""
        # Empty initialization
        ch = ConsistentHash()
        self.assertEqual(len(ch.ring), 0)
        self.assertEqual(len(ch.sorted_keys), 0)
        
        # Initialize with nodes
        nodes = ["node1", "node2", "node3"]
        ch = ConsistentHash(nodes)
        self.assertEqual(len(ch.sorted_keys), len(nodes) * ch.replicas)
    
    def test_add_node(self):
        """Test adding a node to the hash ring"""
        ch = ConsistentHash()
        ch.add_node("node1")
        self.assertEqual(len(ch.sorted_keys), ch.replicas)
        
        # Add another node
        ch.add_node("node2")
        self.assertEqual(len(ch.sorted_keys), 2 * ch.replicas)
    
    def test_remove_node(self):
        """Test removing a node from the hash ring"""
        ch = ConsistentHash(["node1", "node2"])
        original_keys = len(ch.sorted_keys)
        
        ch.remove_node("node1")
        self.assertEqual(len(ch.sorted_keys), original_keys - ch.replicas)
    
    def test_get_node(self):
        """Test getting a node for a key"""
        ch = ConsistentHash(["node1", "node2", "node3"])
        
        # Key should map to a node
        node = ch.get_node("test_key")
        self.assertIn(node, ["node1", "node2", "node3"])
        
        # Same key should always map to the same node
        node2 = ch.get_node("test_key")
        self.assertEqual(node, node2)
    
    def test_distribution(self):
        """Test that keys are distributed fairly evenly"""
        ch = ConsistentHash(["node1", "node2", "node3", "node4"])
        
        # Generate a bunch of keys
        keys = [f"key{i}" for i in range(1000)]
        
        # Count assignments
        counts = {"node1": 0, "node2": 0, "node3": 0, "node4": 0}
        for key in keys:
            node = ch.get_node(key)
            counts[node] += 1
        
        # Check that each node got a reasonable number of keys
        # This is probabilistic, but with 1000 keys, each node should get roughly 250
        # Allow a reasonable margin of error (e.g., +/- 15%)
        for node, count in counts.items():
            self.assertTrue(200 <= count <= 300, 
                          f"Node {node} got {count} keys, expected around 250")
    
    def test_node_removal_impact(self):
        """Test that removing a node doesn't affect most key mappings"""
        nodes = ["node1", "node2", "node3", "node4"]
        ch = ConsistentHash(nodes)
        
        # Generate keys
        keys = [f"key{i}" for i in range(100)]
        
        # Get initial mappings
        initial_mappings = {key: ch.get_node(key) for key in keys}
        
        # Remove a node
        node_to_remove = "node3"
        ch.remove_node(node_to_remove)
        
        # Get new mappings
        new_mappings = {key: ch.get_node(key) for key in keys}
        
        # Count how many keys changed nodes
        changed_count = sum(1 for key in keys if initial_mappings[key] == node_to_remove)
        unchanged_count = sum(1 for key in keys 
                            if initial_mappings[key] != node_to_remove and 
                               initial_mappings[key] == new_mappings[key])
        
        # All keys previously mapped to the removed node should be remapped
        # All other keys should remain with their original nodes
        self.assertEqual(unchanged_count, 
                        sum(1 for key in keys if initial_mappings[key] != node_to_remove))


if __name__ == "__main__":
    unittest.main() 