"""
PyKV Load Tester - Performance benchmarking tool
"""
import time
import random
import string
import asyncio
import argparse
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

import aiohttp


class LoadTester:
    """Load testing tool for PyKV"""
    
    def __init__(self, host="localhost", port=3000, num_workers=10):
        self.base_url = f"http://{host}:{port}"
        self.num_workers = num_workers
        self.reset_results()
        
    def reset_results(self):
        """Reset test results"""
        self.results = {
            "put": defaultdict(list),
            "get": defaultdict(list),
            "delete": defaultdict(list)
        }
        
    def _random_key(self, length=8):
        """Generate a random key"""
        return ''.join(random.choices(string.ascii_lowercase, k=length))
        
    def _random_value(self, length=64):
        """Generate a random value"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
    async def run_test(self, num_operations: int, value_size: int, test_type: Optional[str] = None):
        """Run the performance test"""
        start_time = time.time()
        
        # Create worker tasks
        tasks = []
        ops_per_worker = num_operations // self.num_workers
        for i in range(self.num_workers):
            tasks.append(self._worker(i, ops_per_worker, value_size, test_type))
            
        # Run all workers concurrently
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate and return results
        results = self._calculate_results(total_time, test_type)
        return results
        
    def _calculate_results(self, total_time: float, test_type: Optional[str] = None):
        """Calculate performance metrics"""
        results = {}
        
        operations = ["put", "get", "delete"] if test_type is None else [test_type]
        
        total_ops = 0
        for op in operations:
            if not self.results[op]["time"]:
                continue
                
            # Calculate statistics
            times = self.results[op]["time"]
            success_count = sum(1 for status in self.results[op]["status"] if status in [200, 201, 204, 302])
            error_count = len(self.results[op]["time"]) - success_count + len(self.results[op].get("errors", []))
            
            op_results = {
                "total": len(times),
                "success": success_count,
                "errors": error_count,
                "avg_time": statistics.mean(times) if times else 0,
                "median_time": statistics.median(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "ops_per_sec": success_count / total_time if total_time > 0 else 0
            }
            
            # Add percentiles
            if times:
                times.sort()
                op_results["p95"] = times[int(len(times) * 0.95)]
                op_results["p99"] = times[int(len(times) * 0.99)]
                
            results[op] = op_results
            total_ops += success_count
            
        # Overall statistics
        results["overall"] = {
            "total_time": total_time,
            "total_operations": total_ops,
            "ops_per_sec": total_ops / total_time if total_time > 0 else 0
        }
        
        return results
        
    def print_results(self, results):
        """Print performance test results in a readable format"""
        print("\n=== PyKV Performance Test Results ===\n")
        
        # Overall results
        print(f"Total time: {results['overall']['total_time']:.2f} seconds")
        print(f"Total operations: {results['overall']['total_operations']}")
        print(f"Overall throughput: {results['overall']['ops_per_sec']:.2f} ops/sec")
        print()
        
        # Results per operation type
        for op in ["put", "get", "delete"]:
            if op in results:
                print(f"=== {op.upper()} Operations ===")
                print(f"Total: {results[op]['total']}")
                print(f"Successful: {results[op]['success']}")
                print(f"Errors: {results[op]['errors']}")
                print(f"Throughput: {results[op]['ops_per_sec']:.2f} ops/sec")
                print(f"Average time: {results[op]['avg_time'] * 1000:.2f} ms")
                print(f"Median time: {results[op]['median_time'] * 1000:.2f} ms")
                print(f"Min time: {results[op]['min_time'] * 1000:.2f} ms")
                print(f"Max time: {results[op]['max_time'] * 1000:.2f} ms")
                print(f"95th percentile: {results[op]['p95'] * 1000:.2f} ms")
                print(f"99th percentile: {results[op]['p99'] * 1000:.2f} ms")
                print()
    
    async def _worker(self, worker_id: int, num_operations: int, value_size: int, test_type: Optional[str] = None):
        """Worker that performs operations"""
        keys = []
        
        # PUT phase
        async with aiohttp.ClientSession() as session:
            # PUT phase
            if test_type is None or test_type == "put":
                for i in range(num_operations):
                    key = f"bench_{worker_id}_{i}"
                    value = self._random_value(value_size)
                    keys.append(key)
                    
                    start_time = time.time()
                    try:
                        async with session.put(f"{self.base_url}/{key}", data=value) as response:
                            end_time = time.time()
                            self.results["put"]["time"].append(end_time - start_time)
                            self.results["put"]["status"].append(response.status)
                    except Exception as e:
                        self.results["put"]["errors"].append(str(e))
            
            # GET phase
            if test_type is None or test_type == "get":
                if not keys and test_type == "get":
                    # Pre-populate keys for get-only test
                    for i in range(num_operations):
                        keys.append(f"bench_{worker_id}_{i}")
                
                random.shuffle(keys)  # Randomize access pattern
                for key in keys:
                    start_time = time.time()
                    try:
                        async with session.get(f"{self.base_url}/{key}", allow_redirects=True) as response:
                            end_time = time.time()
                            self.results["get"]["time"].append(end_time - start_time)
                            self.results["get"]["status"].append(response.status)
                    except Exception as e:
                        self.results["get"]["errors"].append(str(e))
            
            # DELETE phase
            if test_type is None or test_type == "delete":
                if not keys and test_type == "delete":
                    # Pre-populate keys for delete-only test
                    for i in range(num_operations):
                        keys.append(f"bench_{worker_id}_{i}")
                
                for key in keys:
                    start_time = time.time()
                    try:
                        async with session.delete(f"{self.base_url}/{key}") as response:
                            end_time = time.time()
                            self.results["delete"]["time"].append(end_time - start_time)
                            self.results["delete"]["status"].append(response.status)
                    except Exception as e:
                        self.results["delete"]["errors"].append(str(e))


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="PyKV Load Tester")
    parser.add_argument("--host", default="localhost", help="PyKV server host")
    parser.add_argument("--port", type=int, default=3000, help="PyKV server port")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers")
    parser.add_argument("--operations", type=int, default=1000, help="Total number of operations")
    parser.add_argument("--value-size", type=int, default=1024, help="Size of values in bytes")
    parser.add_argument("--test-type", choices=["put", "get", "delete"], help="Type of test to run (default: all)")
    parser.add_argument("--prepare", action="store_true", help="Prepare data for get/delete tests")
    
    args = parser.parse_args()
    
    tester = LoadTester(args.host, args.port, args.workers)
    
    # Prepare data if needed
    if args.prepare or (args.test_type in ["get", "delete"]):
        print("Preparing data (putting keys)...")
        tester.reset_results()
        await tester.run_test(args.operations, args.value_size, "put")
        print("Data preparation complete")
        
    # Run the actual test
    if args.prepare:
        return
        
    print(f"\nRunning {'full' if args.test_type is None else args.test_type} test with:")
    print(f"- {args.workers} workers")
    print(f"- {args.operations} operations")
    print(f"- {args.value_size} bytes per value")
    
    tester.reset_results()
    results = await tester.run_test(args.operations, args.value_size, args.test_type)
    tester.print_results(results)


if __name__ == "__main__":
    asyncio.run(main()) 