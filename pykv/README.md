# PyKV - A Mini Key-Value Store

A lightweight, distributed key-value store written in Python, inspired by Redis and minikeyvalue, but under 1000 lines of code.

## Features

- **Simple HTTP API**
  - GET/PUT/DELETE/UNLINK operations
  - Support for batch operations (MGET/MSET)
  - List keys with prefix support
- **Storage Capabilities**
  - Handles values from small strings to large files (1MB-1GB optimized)
  - Supports various data types (strings, numbers, binary data, lists, dictionaries)
  - Optional compression for large values
- **Distributed Architecture**

  - Consistent hashing for balanced data distribution
  - Optional replication for fault tolerance
  - Rebalancing capabilities when adding/removing nodes

- **Performance Focused**
  - Asynchronous I/O for handling many concurrent connections
  - Efficient memory usage with optional disk overflow
  - Index-based lookups for fast retrieval

## HTTP API

```
# Put a value
curl -v -L -X PUT -d "bigswag" localhost:3000/wehave

# Get a value
curl -v -L localhost:3000/wehave

# Delete a key
curl -v -L -X DELETE localhost:3000/wehave

# Virtual delete (unlink)
curl -v -L -X UNLINK localhost:3000/wehave

# List keys with prefix
curl -v -L localhost:3000/we?list

# List unlinked keys
curl -v -L localhost:3000/?unlinked

# Put a file
curl -v -L -X PUT -T /path/to/local/file.txt localhost:3000/file.txt

# Get a file
curl -v -L -o /path/to/local/file.txt localhost:3000/file.txt

# Batch operations
curl -v -L -X PUT -d '{"key1":"value1","key2":"value2"}' localhost:3000/mset
curl -v -L -X GET -d '["key1","key2"]' localhost:3000/mget
```

## Architecture

PyKV uses a two-tier architecture:

1. **Master Server**: Handles routing, metadata, and consistent hashing
2. **Volume Servers**: Store the actual data (can use nginx or python http default server for this)

## Implementation Phases

### Phase 1: Core Functionality

- Basic HTTP server with GET/PUT/DELETE operations
- In-memory storage with simple file persistence
- Initial performance benchmarking

### Phase 2: Distribution

- Implement consistent hashing
- Add volume servers support
- Add replication capabilities

### Phase 3: Advanced Features

- Efficient indexing (LevelDB-inspired)
- Batch operations (MGET/MSET)
- Unlink and garbage collection
- Metrics and monitoring

## Performance Goals

- 3,000+ operations/sec for small values
- Efficient handling of large files
- Low latency for key lookups (<5ms)

## Implementation Notes

- Use `asyncio` for asynchronous I/O
- Consider `LRU` caching for frequently accessed keys
- Use binary format for on-disk storage with checksums
- Implement robust error handling and recovery

## Project Structure

pykv/
├── pykv/
│ ├── **init**.py # Package initialization
│ ├── common/ # Shared code
│ │ ├── **init**.py
│ │ ├── config.py # Configuration management
│ │ ├── consistent_hash.py # Consistent hashing implementation
│ │ └── utils.py # Utility functions
│ │
│ ├── master/ # Master server code
│ │ ├── **init**.py
│ │ ├── server.py # Master server implementation
│ │ └── metadata.py # Metadata management
│ │
│ ├── volume/ # Volume server code
│ │ ├── **init**.py
│ │ └── server.py # Volume server implementation
│ │
│ └── client/ # Client code
│ ├── **init**.py
│ ├── cli.py # Command-line interface
│ └── api.py # Client API
│
├── tests/ # Unit and integration tests
│ ├── test_consistent_hash.py
│ ├── test_master.py
│ └── test_volume.py
│
├── benchmarks/ # Performance benchmarks
│ └── loadtest.py
│
├── docs/ # Documentation
│
├── scripts/ # Helper scripts
│ └── setup.py # Project setup script
│
├── setup.py # Package setup
└── README.md # Project documentation

Module Responsibilities
Common Components

- config.py
  Configuration loading/saving
  Default configurations
  Environment variable handling

- consistent_hash.py
  Consistent hashing ring implementation
  Node management (add/remove)
  Key mapping

- utils.py
  Shared utility functions
  Error handling
  Logging setup

### Master Server

- server.py
  HTTP API implementation
  Request routing
  Client redirection

- metadata.py
  Key-to-volume mapping
  Persistence of metadata
  Handling unlinked keys

### Volume Server

- server.py
  Storage implementation
  File handling
  Data retrieval

### Client

- api.py
  Client library for programmatic access
  Error handling
  Connection management

- cli.py
  Command-line interface
  Argument parsing
  User interaction

### Implementation Sequence

Follow this sequence for a smooth implementation process:

Phase 1: Core Infrastructure

Implement config.py for configuration management
Implement consistent_hash.py for key distribution
Create basic HTTP server structure

Phase 2: Single-Node Functionality

Implement in-memory key-value operations
Add basic persistence
Implement API endpoints

Phase 3: Distribution

Implement master/volume server separation
Add redirection logic
Add metadata tracking

Phase 4: Advanced Features

Add batch operations
Implement unlink functionality
Add prefix scanning

Phase 5: Performance & Robustness

Add performance optimizations
Implement error handling
Add monitoring and metrics

## Tests

Run the tests with pytest:

```bash
pytest
```

Or run a specific test:

```bash
pytest tests/test_consistent_hash.py
```

```python
# Run the script to create project structure
python setup.py --dir my_kv_store

# Change to the project directory
cd my_kv_store

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Start the master server
python -m pykv.master.server

# Start a volume server (in another terminal)
python -m pykv.volume.server --port 3001 --data-dir ./data1
```

~ More
Removing of duplicate files-:

Considerations for Implementation

- Performance: For large files, calculate hashes incrementally to avoid loading entire files into memory
- Fault tolerance: Ensure reference counts stay consistent even during crashes
- Chunking: Consider content-based chunking for partial deduplication of large files with small differences
- Compression: Apply compression before deduplication for better space savings

  pykv/
  ├── pykv/
  │ ├── common/
  │ │ └── dedup.py # Deduplication utilities
  │ ├── volume/
  │ │ └── storage.py # Content-addressable storage
  │ └── master/
  │ └── dedup_stats.py # Deduplication statistics
