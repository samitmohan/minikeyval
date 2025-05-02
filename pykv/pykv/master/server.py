"""
Master server implementation for PyKV
"""
import os
import json
import asyncio
import aiohttp
import uvicorn
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from pykv.common.config import load_config
from pykv.common.consistent_hash import ConsistentHash
from pykv.common.utils import setup_logging
from pykv.master.metadata import MetadataManager


# Models for request/response data
class BatchKeyValue(BaseModel):
    """Model for batch set operations"""
    keys_values: Dict[str, str]


class BatchKeys(BaseModel):
    """Model for batch get operations"""
    keys: List[str]


class VolumeServer:
    """Representation of a volume server"""
    
    def __init__(self, host, port, weight=1):
        self.host = host
        self.port = port
        self.weight = weight
        self.id = f"{host}:{port}"
        self.url = f"http://{host}:{port}"
    
    async def is_alive(self):
        """Check if the volume server is responsive"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.url}/health", timeout=1) as response:
                    return response.status == 200
        except:
            return False


class MasterServer:
    """Master server that manages routing and metadata"""
    
    def __init__(self, config):
        self.app = FastAPI(title="PyKV Master Server")
        self.config = config
        self.volume_servers = []
        self.hash_ring = ConsistentHash()
        self.logger = setup_logging()
        self.metadata_manager = MetadataManager(config["data_dir"])
        
        # Initialize volume servers
        for vs_config in config["volume_servers"]:
            vs = VolumeServer(vs_config["host"], vs_config["port"], vs_config["weight"])
            self.volume_servers.append(vs)
            self.hash_ring.add_node(vs.id)
        
        # Set up routes
        self.setup_routes()
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.join(config["data_dir"], "metadata"), exist_ok=True)
        
    def setup_routes(self):
        """Set up the API routes"""
        @self.app.get("/{key}")
        async def get_key(key: str, request: Request):
            # Special case for listing keys
            if "list" in request.query_params:
                return await self.list_keys_with_prefix(key)
                
            # Special case for listing unlinked keys
            if key == "" and "unlinked" in request.query_params:
                return list(self.metadata_manager.unlinked_keys)
            
            # Normal key retrieval
            volume_id = self.metadata_manager.get_volume_for_key(key)
            if not volume_id:
                raise HTTPException(status_code=404, detail="Key not found")
                
            if self.metadata_manager.is_unlinked(key):
                raise HTTPException(status_code=404, detail="Key has been unlinked")
                
            for vs in self.volume_servers:
                if vs.id == volume_id:
                    # Redirect to the volume server
                    return RedirectResponse(url=f"{vs.url}/{key}", status_code=302)
                    
            raise HTTPException(status_code=500, detail="Volume server not found")
            
        @self.app.put("/{key}")
        async def put_key(key: str, request: Request):
            # Check if key already exists
            if self.metadata_manager.get_volume_for_key(key) and not self.metadata_manager.is_unlinked(key):
                return JSONResponse(status_code=403, content={"detail": "Key already exists"})
                
            # Read body content
            body = await request.body()
            
            # Determine which volume server should store this key
            volume_id = self.hash_ring.get_node(key)
            self.metadata_manager.set_volume_for_key(key, volume_id)
            
            # Save metadata
            await self.metadata_manager.save()
            
            # Forward to volume server
            volume_url = None
            for vs in self.volume_servers:
                if vs.id == volume_id:
                    volume_url = vs.url
                    break
                    
            if not volume_url:
                raise HTTPException(status_code=500, detail="Volume server not available")
                
            # Forward the request to volume server
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{volume_url}/{key}", data=body) as response:
                    # Return the volume server's response
                    return Response(
                        content=await response.read(),
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
            
        @self.app.delete("/{key}")
        async def delete_key(key: str):
            volume_id = self.metadata_manager.get_volume_for_key(key)
            if not volume_id:
                raise HTTPException(status_code=404, detail="Key not found")
                
            volume_url = None
            
            for vs in self.volume_servers:
                if vs.id == volume_id:
                    volume_url = vs.url
                    break
                    
            if not volume_url:
                raise HTTPException(status_code=500, detail="Volume server not available")
                
            # Forward the request to volume server
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{volume_url}/{key}") as response:
                    if response.status == 204:
                        # Remove from metadata
                        self.metadata_manager.delete_key(key)
                        await self.metadata_manager.save()
                        
                    # Return the volume server's response
                    return Response(
                        content=await response.read(),
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
                    
        @self.app.request("/{key}", method="UNLINK")
        async def unlink_key(key: str):
            if not self.metadata_manager.get_volume_for_key(key):
                raise HTTPException(status_code=404, detail="Key not found")
                
            # Mark as unlinked but keep the metadata
            if self.metadata_manager.unlink_key(key):
                await self.metadata_manager.save()
                return Response(status_code=204)
            else:
                raise HTTPException(status_code=404, detail="Key not found")
            
        @self.app.post("/mset")
        async def mset(batch: BatchKeyValue):
            results = {}
            tasks = []
            
            for key, value in batch.keys_values.items():
                # Check if key exists
                if self.metadata_manager.get_volume_for_key(key) and not self.metadata_manager.is_unlinked(key):
                    results[key] = {"status": "error", "message": "Key already exists"}
                    continue
                    
                # Determine which volume server should store this key
                volume_id = self.hash_ring.get_node(key)
                self.metadata_manager.set_volume_for_key(key, volume_id)
                
                # Get volume URL
                volume_url = None
                for vs in self.volume_servers:
                    if vs.id == volume_id:
                        volume_url = vs.url
                        break
                        
                if not volume_url:
                    results[key] = {"status": "error", "message": "Volume server not available"}
                    continue
                    
                # Create task for this key-value pair
                tasks.append(self.put_value(key, value, volume_url))
                
            # Wait for all tasks to complete
            task_results = await asyncio.gather(*tasks)
            
            # Combine results
            for key, status, message in task_results:
                results[key] = {"status": status, "message": message}
                
            # Save metadata
            await self.metadata_manager.save()
                
            return results
            
        async def put_value(key, value, url):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.put(f"{url}/{key}", data=value) as response:
                        if response.status == 201:
                            return key, "success", "Created"
                        else:
                            return key, "error", f"Status: {response.status}"
            except Exception as e:
                return key, "error", str(e)
                
        @self.app.post("/mget")
        async def mget(batch: BatchKeys):
            results = {}
            tasks = []
            
            for key in batch.keys:
                volume_id = self.metadata_manager.get_volume_for_key(key)
                
                if not volume_id or self.metadata_manager.is_unlinked(key):
                    results[key] = {"status": "error", "message": "Key not found"}
                    continue
                    
                # Get volume URL
                volume_url = None
                for vs in self.volume_servers:
                    if vs.id == volume_id:
                        volume_url = vs.url
                        break
                        
                if not volume_url:
                    results[key] = {"status": "error", "message": "Volume server not available"}
                    continue
                    
                # Create task for this key
                tasks.append(self.get_value(key, volume_url))
                
            # Wait for all tasks to complete
            task_results = await asyncio.gather(*tasks)
            
            # Combine results
            for key, status, value_or_message in task_results:
                if status == "success":
                    results[key] = {"status": status, "value": value_or_message}
                else:
                    results[key] = {"status": status, "message": value_or_message}
                
            return results
            
        async def get_value(key, url):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/{key}") as response:
                        if response.status == 200:
                            value = await response.text()
                            return key, "success", value
                        else:
                            return key, "error", f"Status: {response.status}"
            except Exception as e:
                return key, "error", str(e)
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok"}
    
    async def list_keys_with_prefix(self, prefix):
        """List all keys with the given prefix"""
        return self.metadata_manager.get_keys_with_prefix(prefix)
    
    async def start(self):
        """Start the master server"""
        # Load metadata
        await self.metadata_manager.load()
        
        # Start volume server monitoring
        asyncio.create_task(self.monitor_volume_servers())
        
        return self.app
    
    async def monitor_volume_servers(self):
        """Periodically check the health of volume servers"""
        while True:
            for vs in self.volume_servers:
                is_alive = await vs.is_alive()
                if not is_alive:
                    self.logger.warning(f"Volume server {vs.id} is not responding")
                    
            # Check every 10 seconds
            await asyncio.sleep(10)


def main():
    """Entry point for the master server"""
    config = load_config()
    server = MasterServer(config)
    
    # Start the server
    uvicorn.run(
        app=server.app,
        host="0.0.0.0",
        port=config["master_port"],
        log_level="info"
    )


if __name__ == "__main__":
    # For development
    asyncio.run(main()) 