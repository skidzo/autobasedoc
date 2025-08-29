#!/usr/bin/env python3
"""
Test runner script that automatically detects available testing capabilities
and runs tests accordingly.
"""

import os
import subprocess
import sys


def check_coverage_available():
    """Check if pytest-cov is available."""
    try:
        subprocess.run([sys.executable, "-c", "import pytest_cov"], 
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, ImportError):
        return False

def main():
    """Run tests with or without coverage based on availability."""
    
    # Set matplotlib backend for headless environments
    os.environ['MPLBACKEND'] = 'Agg'
    
    print("🧪 Running autobasedoc tests...")
    
    if check_coverage_available():
        print("📊 Coverage tools detected - running with coverage report")
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=autobasedoc",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "-v"
        ]
    else:
        print("⚡ Running basic tests (no coverage)")
        cmd = [sys.executable, "-m", "pytest", "-q"]
    
    # Run the tests
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
