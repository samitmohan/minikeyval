"""
Volume server implementation for PyKV
"""
import os
import asyncio
import aiofiles
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from pykv.common.config import load_config
from pykv.common.utils import setup_logging, ensure_directory


class VolumeServer:
    """Volume server that stores the actual data"""
    
    def __init__(self, config, port=None):
        self.app = FastAPI(title="PyKV Volume Server")
        self.config = config
        self.port = port or 3001  # Default port if not specified
        self.data_dir = os.path.join(config["data_dir"], f"volume_{self.port}")
        self.logger = setup_logging()
        
        # Ensure data directory exists
        ensure_directory(self.data_dir)
        
        # Set up routes
        self.setup_routes()
        
    def setup_routes(self):
        """Set up the API routes"""
        @self.app.get("/{key}")
        async def get_key(key: str):
            file_path = os.path.join(self.data_dir, key)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Key not found")
                
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    data = await f.read()
                return Response(content=data, status_code=200)
            except Exception as e:
                self.logger.error(f"Error reading key {key}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
            
        @self.app.put("/{key}")
        async def put_key(key: str, request: Request):
            file_path = os.path.join(self.data_dir, key)
            
            # Read body content
            body = await request.body()
            
            try:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(body)
                return Response(status_code=201)
            except Exception as e:
                self.logger.error(f"Error writing key {key}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
            
        @self.app.delete("/{key}")
        async def delete_key(key: str):
            file_path = os.path.join(self.data_dir, key)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Key not found")
                
            try:
                os.remove(file_path)
                return Response(status_code=204)
            except Exception as e:
                self.logger.error(f"Error deleting key {key}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/health")
        async def health_check():
            # Check disk space
            try:
                # Simple check if directory is writable
                test_file = os.path.join(self.data_dir, ".health_check")
                async with aiofiles.open(test_file, 'w') as f:
                    await f.write("ok")
                os.remove(test_file)
                
                # TODO: Add more sophisticated health checks like disk space
                
                return {"status": "ok"}
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return {"status": "error", "detail": str(e)}, 500
    
    async def start(self):
        """Start the volume server"""
        return self.app


def main():
    """Entry point for the volume server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PyKV Volume Server")
    parser.add_argument("--port", type=int, default=3001, help="Port to listen on")
    parser.add_argument("--config", help="Path to config file")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    server = VolumeServer(config, args.port)
    
    # Start the server
    uvicorn.run(
        app=server.app,
        host="0.0.0.0",
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    # For development
    main() 