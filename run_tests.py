#!/usr/bin/env python3
"""
TestRunner execution script for Electrum-Dash tests
Handles parallel test execution, result aggregation, and reporting
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import multiprocessing


class TestRunner:
    def __init__(self):
        self.test_root = Path("electrum_dash/tests")
        self.results_dir = Path("test-results")
        self.metrics_dir = Path("test-metrics")
        self.results_dir.mkdir(exist_ok=True)
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Test categories for organized execution
        self.test_categories = {
            "unit": [
                "test_bitcoin.py",
                "test_util.py", 
                "test_mnemonic.py",
                "test_simple_config.py"
            ],
            "dash_specific": [
                "test_dash_tx.py",
                "test_dash_ps.py", 
                "test_dash_msg.py",
                "test_protx.py"
            ],
            "wallet": [
                "test_wallet.py",
                "test_wallet_db.py",
                "test_wallet_vertical.py",
                "test_storage.py",
                "test_storage_upgrade.py"
            ],
            "network": [
                "test_network.py",
                "test_blockchain.py",
                "test_verifier.py"
            ],
            "integration": [
                "test_transaction.py",
                "test_psbt.py",
                "test_commands.py",
                "test_base_wizard.py"
            ]
        }
    
    def run_test_suite(self, category: str, tests: List[str], 
                      parallel: bool = True) -> Dict:
        """Run a specific test suite category"""
        print(f"\n{'='*60}")
        print(f"Running {category.upper()} tests")
        print(f"{'='*60}")
        
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"{category}_{timestamp}.json"
        
        # Build pytest command
        test_paths = [str(self.test_root / test) for test in tests 
                     if (self.test_root / test).exists()]
        
        if not test_paths:
            print(f"No tests found for category: {category}")
            return {"category": category, "status": "skipped", "tests": 0}
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-c", ".test-config/pytest.ini",
            "--json-report",
            f"--json-report-file={result_file}",
            f"--junit-xml=test-results/{category}_{timestamp}.xml"
        ]
        
        # Add parallel execution if enabled and pytest-xdist available
        if parallel and self._check_xdist_available():
            cpu_count = multiprocessing.cpu_count()
            workers = max(1, cpu_count - 1)  # Leave one CPU free
            cmd.extend(["-n", str(workers)])
            print(f"Running tests in parallel with {workers} workers")
        
        cmd.extend(test_paths)
        
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # Parse results
        test_results = {
            "category": category,
            "timestamp": timestamp,
            "duration": duration,
            "return_code": result.returncode,
            "status": "passed" if result.returncode == 0 else "failed"
        }
        
        # Try to load detailed results from JSON report
        if result_file.exists():
            try:
                with open(result_file) as f:
                    json_report = json.load(f)
                    test_results.update({
                        "total": json_report.get("summary", {}).get("total", 0),
                        "passed": json_report.get("summary", {}).get("passed", 0),
                        "failed": json_report.get("summary", {}).get("failed", 0),
                        "skipped": json_report.get("summary", {}).get("skipped", 0),
                        "errors": json_report.get("summary", {}).get("error", 0)
                    })
            except Exception as e:
                print(f"Warning: Could not parse JSON report: {e}")
        
        # Print summary
        print(f"\n{category.upper()} Results:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Status: {test_results['status']}")
        if "total" in test_results:
            print(f"  Total: {test_results['total']}")
            print(f"  Passed: {test_results['passed']}")
            print(f"  Failed: {test_results['failed']}")
            print(f"  Skipped: {test_results['skipped']}")
        
        return test_results
    
    def _check_xdist_available(self) -> bool:
        """Check if pytest-xdist is available for parallel execution"""
        try:
            import pytest_xdist
            return True
        except ImportError:
            return False
    
    def run_all_tests(self, parallel: bool = True, 
                     categories: Optional[List[str]] = None) -> Dict:
        """Run all test categories or specific ones"""
        if categories is None:
            categories = list(self.test_categories.keys())
        
        print(f"TestRunner starting at {datetime.now()}")
        print(f"Running categories: {', '.join(categories)}")
        print(f"Parallel execution: {parallel and self._check_xdist_available()}")
        
        all_results = {
            "start_time": datetime.now().isoformat(),
            "categories": {},
            "summary": {
                "total_duration": 0,
                "total_tests": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0
            }
        }
        
        # Run each category
        for category in categories:
            if category in self.test_categories:
                results = self.run_test_suite(
                    category, 
                    self.test_categories[category],
                    parallel
                )
                all_results["categories"][category] = results
                
                # Update summary
                all_results["summary"]["total_duration"] += results.get("duration", 0)
                if "total" in results:
                    all_results["summary"]["total_tests"] += results["total"]
                    all_results["summary"]["total_passed"] += results["passed"]
                    all_results["summary"]["total_failed"] += results["failed"]
                    all_results["summary"]["total_skipped"] += results["skipped"]
        
        all_results["end_time"] = datetime.now().isoformat()
        
        # Save summary report
        summary_file = self.results_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Print final summary
        print(f"\n{'='*60}")
        print("FINAL TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Duration: {all_results['summary']['total_duration']:.2f}s")
        print(f"Total Tests: {all_results['summary']['total_tests']}")
        print(f"Passed: {all_results['summary']['total_passed']}")
        print(f"Failed: {all_results['summary']['total_failed']}")
        print(f"Skipped: {all_results['summary']['total_skipped']}")
        print(f"\nDetailed results saved to: {summary_file}")
        
        return all_results


def main():
    """Main entry point for test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Electrum-Dash Test Runner")
    parser.add_argument("--categories", "-c", nargs="+", 
                       help="Test categories to run (default: all)")
    parser.add_argument("--no-parallel", action="store_true",
                       help="Disable parallel test execution")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install test dependencies first")
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", 
                       "pytest", "pytest-cov", "pytest-html", 
                       "pytest-json-report", "pytest-xdist"],
                      check=True)
    
    # Run tests
    runner = TestRunner()
    results = runner.run_all_tests(
        parallel=not args.no_parallel,
        categories=args.categories
    )
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["total_failed"] == 0 else 1)


if __name__ == "__main__":
    main()