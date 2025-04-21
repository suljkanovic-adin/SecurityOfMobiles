# native_detector.py

import os
import logging
from typing import List, Dict, Optional, NamedTuple
import re

# Set up logging
logger = logging.getLogger(__name__)

class NativeLibInfo(NamedTuple):
    """Information about a native library."""
    name: str
    architecture: str  # e.g., 'armeabi-v7a', 'x86', etc.
    path: str          # Path relative to the APK root

def list_native_libs(decompile_dir: str) -> List[NativeLibInfo]:
    """
    List native libraries (.so files) included in the APK.
    
    Args:
        decompile_dir: Path to the decompiled APK directory
        
    Returns:
        List of NativeLibInfo objects representing native libraries
    """
    logger.info(f"Scanning for native libraries in {decompile_dir}")
    
    results: List[NativeLibInfo] = []
    lib_dir = os.path.join(decompile_dir, "lib")
    
    if not os.path.isdir(lib_dir):
        logger.debug(f"No 'lib' directory found at {lib_dir}")
        return results
    
    # Common Android architectures
    known_architectures = {
        "armeabi-v7a": "32-bit ARM",
        "arm64-v8a": "64-bit ARM",
        "x86": "32-bit x86",
        "x86_64": "64-bit x86",
        "armeabi": "Legacy ARM",  # Deprecated but still found in some apps
        "mips": "MIPS",          # Very rare, effectively deprecated
        "mips64": "MIPS64"       # Very rare, effectively deprecated
    }
    
    # Walk through the lib directory
    for arch_dir in os.listdir(lib_dir):
        arch_path = os.path.join(lib_dir, arch_dir)
        
        # Skip non-directories or unknown architectures
        if not os.path.isdir(arch_path):
            continue
            
        architecture = arch_dir  # e.g., "armeabi-v7a"
        
        # List .so files in this architecture directory
        for file in os.listdir(arch_path):
            if file.endswith(".so"):
                lib_path = os.path.join("lib", arch_dir, file)
                results.append(NativeLibInfo(
                    name=file,
                    architecture=architecture,
                    path=lib_path
                ))
    
    # Sort results by name for consistent output
    results.sort(key=lambda lib: lib.name)
    
    logger.info(f"Found {len(results)} native libraries across {len({lib.architecture for lib in results})} architectures")
    
    return results

def analyze_native_function_usage(decompile_dir: str) -> Dict[str, int]:
    """
    Analyze how often each native library is referenced in code.
    
    Args:
        decompile_dir: Path to the decompiled APK directory
        
    Returns:
        Dictionary mapping library names to reference counts
    """
    usage_counts: Dict[str, int] = {}
    
    # Get all native libraries first
    libraries = list_native_libs(decompile_dir)
    if not libraries:
        return usage_counts
    
    # Create a dictionary of library base names (without .so extension)
    lib_names = {os.path.splitext(lib.name)[0]: lib.name for lib in libraries}
    
    # Pattern to find System.loadLibrary calls
    load_library_pattern = re.compile(r'const-string [^,]+, "([^"\\]*(?:\\.[^"\\]*)*)"[^\n]*?\n.*?invoke-static[^\n]*?System;->loadLibrary')
    
    # Search through smali files for references
    smali_dirs = [os.path.join(decompile_dir, "smali")]
    
    # Check for multidex
    for i in range(2, 10):
        additional_dir = os.path.join(decompile_dir, f"smali_classes{i}")
        if os.path.isdir(additional_dir):
            smali_dirs.append(additional_dir)
    
    # Initialize counts for all libraries
    for lib_name in lib_names.values():
        usage_counts[lib_name] = 0
    
    # Scan smali files for library loading
    for smali_dir in smali_dirs:
        if not os.path.isdir(smali_dir):
            continue
            
        for root, _, files in os.walk(smali_dir):
            for file in files:
                if not file.endswith(".smali"):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Look for System.loadLibrary calls
                        for match in load_library_pattern.finditer(content):
                            lib_name = match.group(1)
                            
                            # Check if this is one of our libraries
                            if lib_name in lib_names:
                                usage_counts[lib_names[lib_name]] += 1
                            elif f"{lib_name}.so" in lib_names.values():
                                usage_counts[f"{lib_name}.so"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    return usage_counts