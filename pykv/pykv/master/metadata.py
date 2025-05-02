"""
Metadata management for the PyKV master server
"""
import os
import json
import asyncio
import aiofiles
from typing import Dict, Set, List, Optional


class MetadataManager:
    """Manages metadata for the PyKV master server"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.metadata_dir = os.path.join(data_dir, "metadata")
        self.metadata_file = os.path.join(self.metadata_dir, "keymap.json")
        self.unlinked_file = os.path.join(self.metadata_dir, "unlinked.json")
        self.metadata = {}  # Maps keys to volume servers
        self.unlinked_keys = set()  # Keys marked as deleted but not physically removed
        
        # Ensure metadata directory exists
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    async def load(self):
        """Load metadata from disk"""
        try:
            # Load key-to-volume mapping
            if os.path.exists(self.metadata_file):
                async with aiofiles.open(self.metadata_file, 'r') as f:
                    content = await f.read()
                    self.metadata = json.loads(content)
            
            # Load unlinked keys
            if os.path.exists(self.unlinked_file):
                async with aiofiles.open(self.unlinked_file, 'r') as f:
                    content = await f.read()
                    self.unlinked_keys = set(json.loads(content))
                    
            return True
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return False
    
    async def save(self):
        """Save metadata to disk"""
        try:
            # Save key-to-volume mapping
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(self.metadata))
            
            # Save unlinked keys
            async with aiofiles.open(self.unlinked_file, 'w') as f:
                await f.write(json.dumps(list(self.unlinked_keys)))
                
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def get_volume_for_key(self, key: str) -> Optional[str]:
        """Get the volume server ID for a key"""
        return self.metadata.get(key)
    
    def set_volume_for_key(self, key: str, volume_id: str):
        """Set the volume server ID for a key"""
        self.metadata[key] = volume_id
        
        # If the key was previously unlinked, remove it from unlinked set
        if key in self.unlinked_keys:
            self.unlinked_keys.remove(key)
    
    def delete_key(self, key: str) -> bool:
        """Delete a key from metadata"""
        if key in self.metadata:
            del self.metadata[key]
            return True
        return False
    
    def unlink_key(self, key: str) -> bool:
        """Mark a key as unlinked"""
        if key in self.metadata:
            self.unlinked_keys.add(key)
            return True
        return False
    
    def is_unlinked(self, key: str) -> bool:
        """Check if a key is unlinked"""
        return key in self.unlinked_keys
    
    def get_keys_with_prefix(self, prefix: str) -> List[str]:
        """Get all keys with a given prefix"""
        return [key for key in self.metadata.keys() 
                if key.startswith(prefix) and key not in self.unlinked_keys] 