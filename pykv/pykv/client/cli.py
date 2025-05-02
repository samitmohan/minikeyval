"""
Command-line interface for PyKV client
"""
import os
import sys
import json
import argparse
import asyncio
from pykv.client.api import PyKVClient


async def main():
    """Command-line interface for PyKV client"""
    parser = argparse.ArgumentParser(description="PyKV Client")
    parser.add_argument("--host", default="localhost", help="PyKV server host")
    parser.add_argument("--port", type=int, default=3000, help="PyKV server port")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # GET command
    get_parser = subparsers.add_parser("get", help="Get a value")
    get_parser.add_argument("key", help="Key to get")
    get_parser.add_argument("--file", "-f", help="Save output to file")
    
    # PUT command
    put_parser = subparsers.add_parser("put", help="Put a value")
    put_parser.add_argument("key", help="Key to put")
    put_parser.add_argument("value", nargs="?", help="Value to put")
    put_parser.add_argument("--file", "-f", help="Read input from file")
    
    # DELETE command
    delete_parser = subparsers.add_parser("delete", help="Delete a key")
    delete_parser.add_argument("key", help="Key to delete")
    
    # UNLINK command
    unlink_parser = subparsers.add_parser("unlink", help="Virtually delete a key")
    unlink_parser.add_argument("key", help="Key to unlink")
    
    # LIST command
    list_parser = subparsers.add_parser("list", help="List keys")
    list_parser.add_argument("prefix", nargs="?", default="", help="Prefix to filter keys")
    
    # UNLINKED command
    subparsers.add_parser("unlinked", help="List unlinked keys")
    
    # MGET command
    mget_parser = subparsers.add_parser("mget", help="Get multiple values")
    mget_parser.add_argument("keys", nargs="+", help="Keys to get")
    
    # MSET command
    mset_parser = subparsers.add_parser("mset", help="Set multiple key-value pairs")
    mset_parser.add_argument("pairs", nargs="+", help="Key-value pairs in the format key=value")
    
    args = parser.parse_args()
    
    client = PyKVClient(args.host, args.port)
    
    if args.command == "get":
        if args.file:
            success = await client.get_file(args.key, args.file)
            if success:
                print(f"Value for key '{args.key}' saved to {args.file}")
        else:
            value = await client.get(args.key)
            if value is not None:
                # Try to decode as UTF-8, fall back to printing as bytes
                try:
                    print(value.decode('utf-8'))
                except UnicodeDecodeError:
                    print(f"Binary data: {len(value)} bytes")
    
    elif args.command == "put":
        if args.file:
            success = await client.put_file(args.key, args.file)
            if success:
                print(f"File {args.file} stored with key '{args.key}'")
        elif args.value is not None:
            success = await client.put(args.key, args.value)
            if success:
                print(f"Key '{args.key}' set successfully")
        else:
            # Read from stdin
            value = sys.stdin.read()
            success = await client.put(args.key, value)
            if success:
                print(f"Key '{args.key}' set successfully")
    
    elif args.command == "delete":
        success = await client.delete(args.key)
        if success:
            print(f"Key '{args.key}' deleted successfully")
    
    elif args.command == "unlink":
        success = await client.unlink(args.key)
        if success:
            print(f"Key '{args.key}' unlinked successfully")
    
    elif args.command == "list":
        keys = await client.list_keys(args.prefix)
        if keys:
            for key in keys:
                print(key)
        else:
            print(f"No keys found with prefix '{args.prefix}'")
    
    elif args.command == "unlinked":
        keys = await client.list_unlinked()
        if keys:
            for key in keys:
                print(key)
        else:
            print("No unlinked keys found")
    
    elif args.command == "mget":
        results = await client.mget(args.keys)
        for key, value in results.items():
            if value is not None:
                try:
                    print(f"{key}: {value.decode('utf-8')}")
                except UnicodeDecodeError:
                    print(f"{key}: (binary data, {len(value)} bytes)")
            else:
                print(f"{key}: Not found")
    
    elif args.command == "mset":
        # Parse key=value pairs
        key_values = {}
        for pair in args.pairs:
            if "=" not in pair:
                print(f"Error: Invalid format for pair '{pair}', expected key=value")
                return
            key, value = pair.split("=", 1)
            key_values[key] = value
            
        results = await client.mset(key_values)
        success_count = sum(1 for success in results.values() if success)
        print(f"Set {success_count}/{len(key_values)} keys successfully")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 