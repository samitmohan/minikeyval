#!/usr/bin/env python3
"""
PyKV Setup Script - Initializes data directories and configuration
"""
import os
import sys
import json
import argparse


def create_data_directories(data_dir, ports):
    """Create data directories for master and volume servers"""
    # Create base data directory
    os.makedirs(data_dir, exist_ok=True)
    print(f"Created data directory: {data_dir}")
    
    # Create metadata directory for master
    metadata_dir = os.path.join(data_dir, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    print(f"Created metadata directory: {metadata_dir}")
    
    # Create directories for volume servers
    for port in ports:
        volume_dir = os.path.join(data_dir, f"volume_{port}")
        os.makedirs(volume_dir, exist_ok=True)
        print(f"Created volume directory: {volume_dir}")


def create_config_file(config_path, master_port, volume_ports, data_dir):
    """Create a configuration file"""
    config = {
        "master_port": master_port,
        "volume_servers": [
            {"host": "localhost", "port": port, "weight": 1}
            for port in volume_ports
        ],
        "replication_factor": 1,
        "data_dir": data_dir
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created configuration file: {config_path}")


def main():
    """Entry point for setup script"""
    parser = argparse.ArgumentParser(description="PyKV Setup Script")
    parser.add_argument("--data-dir", default="./data", help="Data directory for PyKV")
    parser.add_argument("--config", default="./pykv.json", help="Path to configuration file")
    parser.add_argument("--master-port", type=int, default=3000, help="Port for master server")
    parser.add_argument("--volume-ports", default="3001,3002", help="Comma-separated ports for volume servers")
    
    args = parser.parse_args()
    
    # Parse volume ports
    volume_ports = [int(port.strip()) for port in args.volume_ports.split(",")]
    
    # Create directories
    create_data_directories(args.data_dir, volume_ports)
    
    # Create configuration file
    create_config_file(args.config, args.master_port, volume_ports, args.data_dir)
    
    print("\nSetup completed successfully!")
    print(f"\nTo start the master server:")
    print(f"  pykv-master --config {args.config}")
    
    print("\nTo start the volume servers:")
    for port in volume_ports:
        print(f"  pykv-volume --port {port} --config {args.config}")
    
    print("\nTo use the client:")
    print(f"  pykv-client --host localhost --port {args.master_port} put mykey \"Hello, World!\"")
    print(f"  pykv-client --host localhost --port {args.master_port} get mykey")


if __name__ == "__main__":
    main() 