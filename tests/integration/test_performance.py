"""Performance benchmarking tests."""

import pytest
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any
import os
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from arxml_analyzer.core.parser.xml_parser import XMLParser
from arxml_analyzer.core.parser.stream_parser import StreamParser
from arxml_analyzer.core.analyzer.type_detector import TypeDetector
from arxml_analyzer.analyzers.ecuc_analyzer import ECUCAnalyzer
from arxml_analyzer.analyzers.swc_analyzer import SWCAnalyzer
from arxml_analyzer.analyzers.interface_analyzer import InterfaceAnalyzer
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


class TestPerformance:
    """Performance and benchmarking tests."""
    
    @pytest.fixture
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return Path(__file__).parent.parent.parent / "data" / "official"
    
    @pytest.fixture
    def test_files(self, data_dir) -> List[Path]:
        """Get all test ARXML files."""
        files = []
        for ext in ["ecuc", "swc", "interface", "diagnostic", "communication", "system"]:
            dir_path = data_dir / ext
            if dir_path.exists():
                files.extend(dir_path.glob("*.arxml"))
        return files
    
    @pytest.fixture
    def analyzers(self):
        """Create analyzer instances."""
        return {
            "ECUC": ECUCAnalyzer(),
            "SWC": SWCAnalyzer(),
            "INTERFACE": InterfaceAnalyzer()
        }
    
    def measure_time(self, func, *args, **kwargs) -> float:
        """Measure execution time of a function."""
        start = time.perf_counter()
        func(*args, **kwargs)
        return time.perf_counter() - start
    
    def measure_memory(self, func, *args, **kwargs) -> Dict[str, float]:
        """Measure memory usage of a function."""
        if not HAS_PSUTIL:
            result = func(*args, **kwargs)
            return {"rss_mb": 0, "vms_mb": 0, "result": result}
            
        process = psutil.Process(os.getpid())
        
        # Force garbage collection
        import gc
        gc.collect()
        
        memory_before = process.memory_info()
        result = func(*args, **kwargs)
        memory_after = process.memory_info()
        
        return {
            "rss_mb": (memory_after.rss - memory_before.rss) / 1024 / 1024,
            "vms_mb": (memory_after.vms - memory_before.vms) / 1024 / 1024,
            "result": result
        }
    
    def test_parser_performance_comparison(self, test_files):
        """Compare performance between XMLParser and StreamParser."""
        if not test_files:
            pytest.skip("No test files available")
        
        xml_parser = XMLParser()
        stream_parser = StreamParser()
        
        results = {
            "xml_parser": [],
            "stream_parser": [],
            "file_sizes": []
        }
        
        # Test with files of different sizes
        test_subset = test_files[:10]  # Test with first 10 files
        
        for file in test_subset:
            file_size_mb = file.stat().st_size / 1024 / 1024
            results["file_sizes"].append(file_size_mb)
            
            # Measure XMLParser
            xml_time = self.measure_time(xml_parser.parse, str(file))
            results["xml_parser"].append(xml_time)
            
            # Measure StreamParser
            stream_time = self.measure_time(stream_parser.parse, str(file))
            results["stream_parser"].append(stream_time)
        
        # Calculate statistics
        print("\n=== Parser Performance Comparison ===")
        print(f"Files tested: {len(test_subset)}")
        print(f"File sizes: {min(results['file_sizes']):.2f}MB - {max(results['file_sizes']):.2f}MB")
        print(f"\nXMLParser:")
        print(f"  Average time: {statistics.mean(results['xml_parser']):.3f}s")
        print(f"  Min time: {min(results['xml_parser']):.3f}s")
        print(f"  Max time: {max(results['xml_parser']):.3f}s")
        print(f"\nStreamParser:")
        print(f"  Average time: {statistics.mean(results['stream_parser']):.3f}s")
        print(f"  Min time: {min(results['stream_parser']):.3f}s")
        print(f"  Max time: {max(results['stream_parser']):.3f}s")
        
        # StreamParser should be more efficient for larger files
        large_files = [i for i, size in enumerate(results['file_sizes']) if size > 0.1]
        if large_files:
            for idx in large_files:
                ratio = results['xml_parser'][idx] / results['stream_parser'][idx]
                print(f"\nFile {test_subset[idx].name} ({results['file_sizes'][idx]:.2f}MB):")
                print(f"  Speed ratio (XML/Stream): {ratio:.2f}x")
    
    def test_analyzer_performance(self, test_files, analyzers):
        """Test performance of different analyzers."""
        if not test_files:
            pytest.skip("No test files available")
        
        analyzer_times = {}
        
        # Test each file and measure analyzer performance
        parser = XMLParser()
        detector = TypeDetector()
        
        for file in test_files[:5]:  # Test first 5 files
            try:
                # Parse the file
                document = parser.parse(str(file))
                
                # Detect type
                detected_types = detector.detect(document)
                if not detected_types:
                    continue
                    
                primary_type = detected_types[0].name
                
                # Find matching analyzer
                if primary_type in analyzers:
                    analyzer = analyzers[primary_type]
                    
                    # Measure analysis time
                    start_time = time.perf_counter()
                    result = analyzer.analyze(document)
                    duration = time.perf_counter() - start_time
                    
                    if primary_type not in analyzer_times:
                        analyzer_times[primary_type] = []
                    analyzer_times[primary_type].append(duration)
            except Exception as e:
                print(f"Error analyzing {file}: {e}")
                continue
        
        # Print performance statistics
        print("\n=== Analyzer Performance ===")
        for analyzer, times in analyzer_times.items():
            if times:
                print(f"\n{analyzer}:")
                print(f"  Runs: {len(times)}")
                print(f"  Average time: {statistics.mean(times):.3f}s")
                print(f"  Min time: {min(times):.3f}s")
                print(f"  Max time: {max(times):.3f}s")
                if len(times) > 1:
                    print(f"  Std dev: {statistics.stdev(times):.3f}s")
    
    def test_parallel_processing_scalability(self, test_files, analyzers):
        """Test scalability of parallel processing."""
        if len(test_files) < 8:
            pytest.skip("Not enough files for scalability test")
        
        file_paths = [str(f) for f in test_files[:8]]
        
        results = {}
        parser = XMLParser()
        
        def analyze_file(file_path):
            """Analyze a single file."""
            try:
                document = parser.parse(file_path)
                detector = TypeDetector()
                detected_types = detector.detect(document)
                if detected_types:
                    primary_type = detected_types[0].name
                    if primary_type in analyzers:
                        return analyzers[primary_type].analyze(document)
            except:
                pass
            return None
        
        # Test with different number of workers
        for num_workers in [1, 2, 4, 8]:
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                list(executor.map(analyze_file, file_paths))
            
            elapsed = time.perf_counter() - start_time
            results[num_workers] = elapsed
        
        # Calculate speedup
        print("\n=== Parallel Processing Scalability ===")
        print(f"Files processed: {len(file_paths)}")
        baseline = results[1]
        
        for workers, elapsed in results.items():
            speedup = baseline / elapsed
            efficiency = speedup / workers * 100
            print(f"\nWorkers: {workers}")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Speedup: {speedup:.2f}x")
            print(f"  Efficiency: {efficiency:.1f}%")
        
        # Check that parallel processing provides speedup
        assert results[2] < results[1], "2 workers should be faster than 1"
        assert results[4] < results[2], "4 workers should be faster than 2"
    
    def test_memory_usage_by_file_size(self, test_files):
        """Test memory usage correlation with file size."""
        if not test_files:
            pytest.skip("No test files available")
        
        parser = XMLParser()
        results = []
        
        # Sort files by size
        sorted_files = sorted(test_files, key=lambda f: f.stat().st_size)[:5]
        
        for file in sorted_files:
            file_size_mb = file.stat().st_size / 1024 / 1024
            
            # Measure memory usage
            mem_info = self.measure_memory(parser.parse, str(file))
            
            results.append({
                "file": file.name,
                "size_mb": file_size_mb,
                "memory_mb": mem_info["rss_mb"]
            })
        
        # Print results
        print("\n=== Memory Usage by File Size ===")
        for res in results:
            ratio = res["memory_mb"] / res["size_mb"] if res["size_mb"] > 0 else 0
            print(f"\n{res['file']}:")
            print(f"  File size: {res['size_mb']:.2f}MB")
            print(f"  Memory used: {res['memory_mb']:.2f}MB")
            print(f"  Memory/Size ratio: {ratio:.2f}x")
        
        # Check that memory usage is reasonable
        for res in results:
            if res["size_mb"] > 0:
                ratio = res["memory_mb"] / res["size_mb"]
                assert ratio < 20, f"Memory usage too high for {res['file']}: {ratio:.2f}x file size"
    
    def test_analysis_throughput(self, test_files, analyzers):
        """Test analysis throughput (files per second)."""
        if not test_files:
            pytest.skip("No test files available")
        
        # Group files by size
        small_files = [f for f in test_files if f.stat().st_size < 100 * 1024]  # < 100KB
        medium_files = [f for f in test_files if 100 * 1024 <= f.stat().st_size < 1024 * 1024]  # 100KB-1MB
        large_files = [f for f in test_files if f.stat().st_size >= 1024 * 1024]  # >= 1MB
        
        results = {}
        
        # Test throughput for different file sizes
        for category, files in [("small", small_files), ("medium", medium_files), ("large", large_files)]:
            if files:
                subset = files[:5]  # Test up to 5 files
                
                parser = XMLParser()
                detector = TypeDetector()
                
                start_time = time.perf_counter()
                for file in subset:
                    try:
                        document = parser.parse(str(file))
                        detected_types = detector.detect(document)
                        if detected_types:
                            primary_type = detected_types[0].name
                            if primary_type in analyzers:
                                analyzers[primary_type].analyze(document)
                    except:
                        pass
                elapsed = time.perf_counter() - start_time
                
                throughput = len(subset) / elapsed
                avg_size_mb = statistics.mean(f.stat().st_size for f in subset) / 1024 / 1024
                
                results[category] = {
                    "count": len(subset),
                    "throughput": throughput,
                    "avg_size_mb": avg_size_mb,
                    "total_time": elapsed
                }
        
        # Print results
        print("\n=== Analysis Throughput ===")
        for category, data in results.items():
            print(f"\n{category.capitalize()} files (avg {data['avg_size_mb']:.2f}MB):")
            print(f"  Files analyzed: {data['count']}")
            print(f"  Total time: {data['total_time']:.2f}s")
            print(f"  Throughput: {data['throughput']:.2f} files/second")
            print(f"  Average time per file: {data['total_time']/data['count']:.2f}s")
    
    def test_cache_effectiveness(self, test_files, analyzers):
        """Test caching effectiveness by analyzing same file multiple times."""
        if not test_files:
            pytest.skip("No test files available")
        
        test_file = str(test_files[0])
        parser = XMLParser()
        detector = TypeDetector()
        
        def analyze():
            document = parser.parse(test_file)
            detected_types = detector.detect(document)
            if detected_types:
                primary_type = detected_types[0].name
                if primary_type in analyzers:
                    return analyzers[primary_type].analyze(document)
            return None
        
        # First run (cold cache)
        start_time = time.perf_counter()
        analyze()
        first_run = time.perf_counter() - start_time
        
        # Second run (warm cache if implemented)
        start_time = time.perf_counter()
        analyze()
        second_run = time.perf_counter() - start_time
        
        # Third run
        start_time = time.perf_counter()
        analyze()
        third_run = time.perf_counter() - start_time
        
        print("\n=== Cache Effectiveness ===")
        print(f"File: {Path(test_file).name}")
        print(f"First run: {first_run:.3f}s")
        print(f"Second run: {second_run:.3f}s")
        print(f"Third run: {third_run:.3f}s")
        
        if second_run < first_run:
            speedup = first_run / second_run
            print(f"Cache speedup: {speedup:.2f}x")
        else:
            print("No cache speedup detected")
    
    @pytest.mark.slow
    def test_stress_test_large_directory(self, data_dir, analyzers):
        """Stress test with analyzing entire directory."""
        import glob
        
        # Get all ARXML files
        arxml_files = list(Path(data_dir).rglob("*.arxml"))
        
        parser = XMLParser()
        detector = TypeDetector()
        
        successful = 0
        failed = 0
        
        # Analyze entire data directory
        start_time = time.perf_counter()
        
        for file in arxml_files:
            try:
                document = parser.parse(str(file))
                detected_types = detector.detect(document)
                if detected_types:
                    primary_type = detected_types[0].name
                    if primary_type in analyzers:
                        result = analyzers[primary_type].analyze(document)
                        if result:
                            successful += 1
                        else:
                            failed += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            except:
                failed += 1
        
        elapsed = time.perf_counter() - start_time
        total_files = successful + failed
        
        print("\n=== Stress Test Results ===")
        print(f"Directory: {data_dir}")
        print(f"Total files: {total_files}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total time: {elapsed:.2f}s")
        if total_files > 0:
            print(f"Average time per file: {elapsed/total_files:.2f}s")
            
            # Check success rate
            success_rate = successful / total_files * 100
            assert success_rate > 50, f"Success rate too low: {success_rate:.1f}%"
            
            # Performance should be reasonable
            assert elapsed / total_files < 5, "Analysis too slow (>5s per file)"