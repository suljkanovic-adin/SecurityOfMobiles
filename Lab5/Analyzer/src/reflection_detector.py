# reflection_detector.py

import os
import re
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ReflectionInfo:
    """Container for reflection detection results."""
    reflection_calls: List[Dict[str, str]] = field(default_factory=list)
    dynamic_loading: List[Dict[str, str]] = field(default_factory=list)
    native_method_calls: List[Dict[str, str]] = field(default_factory=list)
    
    @property
    def has_reflection(self) -> bool:
        """Check if any reflection was detected."""
        return len(self.reflection_calls) > 0
        
    @property
    def has_dynamic_loading(self) -> bool:
        """Check if any dynamic loading was detected."""
        return len(self.dynamic_loading) > 0
        
    @property
    def has_native_methods(self) -> bool:
        """Check if any native method calls were detected."""
        return len(self.native_method_calls) > 0
        
    @property
    def total_issues(self) -> int:
        """Get total number of reflection-related issues."""
        return len(self.reflection_calls) + len(self.dynamic_loading) + len(self.native_method_calls)

def detect_reflection(decompile_dir: str) -> ReflectionInfo:
    """
    Detect use of Java reflection, dynamic class loading, and native method calls.
    
    Args:
        decompile_dir: Path to the decompiled APK directory
        
    Returns:
        ReflectionInfo object containing detected reflection usage
    """
    logger.info(f"Scanning for reflection in {decompile_dir}")
    
    results = ReflectionInfo()
    
    # Scan smali files for reflection
    smali_dir = os.path.join(decompile_dir, "smali")
    if not os.path.isdir(smali_dir):
        logger.warning(f"No smali directory found at {smali_dir}")
        return results
    
    # Check for multiple smali directories (multidex apps)
    smali_dirs = [smali_dir]
    for i in range(2, 10):  # Check for smali_classes2 through smali_classes9
        additional_dir = os.path.join(decompile_dir, f"smali_classes{i}")
        if os.path.isdir(additional_dir):
            smali_dirs.append(additional_dir)
    
    # Patterns to search for
    reflection_patterns = {
        # Java reflection API methods
        "Class.forName": re.compile(r'invoke-static {[^}]*}, Ljava/lang/Class;->forName\(Ljava/lang/String;\)Ljava/lang/Class;'),
        "Class.getDeclaredMethod": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/Class;->getDeclaredMethod\(Ljava/lang/String;'),
        "Class.getMethod": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/Class;->getMethod\(Ljava/lang/String;'),
        "getDeclaredField": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/Class;->getDeclaredField\(Ljava/lang/String;\)'),
        "getField": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/Class;->getField\(Ljava/lang/String;\)'),
        "Method.invoke": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/reflect/Method;->invoke\(Ljava/lang/Object;\[Ljava/lang/Object;\)Ljava/lang/Object;'),
        "Constructor.newInstance": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/reflect/Constructor;->newInstance\('),
    }
    
    dynamic_loading_patterns = {
        # Dynamic class loading
        "DexClassLoader": re.compile(r'new-instance [^,]+, Ldalvik/system/DexClassLoader;'),
        "PathClassLoader": re.compile(r'new-instance [^,]+, Ldalvik/system/PathClassLoader;'),
        "InMemoryDexClassLoader": re.compile(r'new-instance [^,]+, Ldalvik/system/InMemoryDexClassLoader;'),
        "ClassLoader.loadClass": re.compile(r'invoke-virtual {[^}]*}, Ljava/lang/ClassLoader;->loadClass\(Ljava/lang/String;\)Ljava/lang/Class;'),
    }
    
    native_patterns = {
        # Native method declarations and JNI calls
        "native method": re.compile(r'\.method.* native '),
        "System.loadLibrary": re.compile(r'invoke-static {[^}]*}, Ljava/lang/System;->loadLibrary\(Ljava/lang/String;\)V'),
        "System.load": re.compile(r'invoke-static {[^}]*}, Ljava/lang/System;->load\(Ljava/lang/String;\)V'),
    }
    
    for smali_dir in smali_dirs:
        # Walk through all smali files
        for root, _, files in os.walk(smali_dir):
            for file in files:
                if not file.endswith(".smali"):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        class_name = extract_class_name(content)
                        
                        # Check for reflection
                        for pattern_name, pattern in reflection_patterns.items():
                            for match in pattern.finditer(content):
                                line_number = content[:match.start()].count('\n') + 1
                                results.reflection_calls.append({
                                    'type': pattern_name,
                                    'class': class_name,
                                    'file': os.path.relpath(file_path, smali_dir),
                                    'line': line_number
                                })
                        
                        # Check for dynamic loading
                        for pattern_name, pattern in dynamic_loading_patterns.items():
                            for match in pattern.finditer(content):
                                line_number = content[:match.start()].count('\n') + 1
                                results.dynamic_loading.append({
                                    'type': pattern_name,
                                    'class': class_name,
                                    'file': os.path.relpath(file_path, smali_dir),
                                    'line': line_number
                                })
                        
                        # Check for native methods
                        for pattern_name, pattern in native_patterns.items():
                            for match in pattern.finditer(content):
                                line_number = content[:match.start()].count('\n') + 1
                                results.native_method_calls.append({
                                    'type': pattern_name,
                                    'class': class_name,
                                    'file': os.path.relpath(file_path, smali_dir),
                                    'line': line_number
                                })
                                
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    logger.info(f"Found {results.total_issues} reflection-related issues: "
               f"{len(results.reflection_calls)} reflection calls, "
               f"{len(results.dynamic_loading)} dynamic loading instances, "
               f"{len(results.native_method_calls)} native method calls")
    
    return results

def extract_class_name(smali_content: str) -> str:
    """Extract the class name from smali file content."""
    class_match = re.search(r'\.class.*?(L[^;]+;)', smali_content)
    if class_match:
        class_name = class_match.group(1)
        # Convert from smali format to Java format
        return class_name.replace('/', '.').replace(';', '').replace('L', '')
    return "Unknown"