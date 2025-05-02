"""
PyKV client API for programmatic access
"""
import os
import json
import asyncio
import aiohttp
import aiofiles
from typing import Dict, List, Optional, Union


class PyKVClient:
    """Client for interacting with PyKV server"""
    
    def __init__(self, host="localhost", port=3000):
        self.base_url = f"http://{host}:{port}"
        
    async def get(self, key: str) -> bytes:
        """Get value for a key"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/{key}", allow_redirects=True) as response:
                if response.status == 200:
                    return await response.read()
                elif response.status == 404:
                    print(f"Error: Key '{key}' not found")
                    return None
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return None
                    
    async def put(self, key: str, value: Union[str, bytes]) -> bool:
        """Put a key-value pair"""
        if isinstance(value, str):
            value = value.encode('utf-8')
            
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.base_url}/{key}", data=value) as response:
                if response.status == 201:
                    return True
                elif response.status == 403:
                    print(f"Error: Key '{key}' already exists")
                    return False
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return False
                    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.base_url}/{key}") as response:
                if response.status == 204:
                    return True
                elif response.status == 404:
                    print(f"Error: Key '{key}' not found")
                    return False
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return False
                    
    async def unlink(self, key: str) -> bool:
        """Virtually delete (unlink) a key"""
        async with aiohttp.ClientSession() as session:
            async with session.request("UNLINK", f"{self.base_url}/{key}") as response:
                if response.status == 204:
                    return True
                elif response.status == 404:
                    print(f"Error: Key '{key}' not found")
                    return False
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return False
                    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys with given prefix"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/{prefix}?list") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return []
                    
    async def list_unlinked(self) -> List[str]:
        """List unlinked keys"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/?unlinked") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return []
                    
    async def mget(self, keys: List[str]) -> Dict[str, bytes]:
        """Get multiple keys at once"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/mget", json={"keys": keys}) as response:
                if response.status == 200:
                    results = await response.json()
                    # Convert successful results to bytes
                    return {k: v["value"].encode('utf-8') if v["status"] == "success" else None 
                            for k, v in results.items()}
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return {}
                    
    async def mset(self, key_values: Dict[str, Union[str, bytes]]) -> Dict[str, bool]:
        """Set multiple key-value pairs at once"""
        # Convert any bytes to strings
        kv_dict = {}
        for k, v in key_values.items():
            if isinstance(v, bytes):
                kv_dict[k] = v.decode('utf-8')
            else:
                kv_dict[k] = v
                
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/mset", json={"keys_values": kv_dict}) as response:
                if response.status == 200:
                    results = await response.json()
                    return {k: v["status"] == "success" for k, v in results.items()}
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return {}
                    
    async def put_file(self, key: str, file_path: str) -> bool:
        """Put a file into the key-value store"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
                
            return await self.put(key, data)
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
            
    async def get_file(self, key: str, file_path: str) -> bool:
        """Get a value and save it to a file"""
        data = await self.get(key)
        if data is None:
            return False
            
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(data)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False 