# strings_extractor.py

import os
import re
import logging
from typing import List, Dict, Set, Optional
import xml.etree.ElementTree as ET

# Set up logging
logger = logging.getLogger(__name__)

def extract_strings(decompile_dir: str) -> List[str]:
    """
    Extract interesting strings from decompiled APK.
    
    This function scans the decompiled APK directory for:
    1. Strings from res/values/strings.xml
    2. URLs and sensitive patterns in smali files
    3. Hardcoded strings in smali files
    
    Args:
        decompile_dir: Path to the decompiled APK directory
        
    Returns:
        List of interesting strings found in the APK
    """
    logger.info(f"Extracting strings from {decompile_dir}")
    
    results: Set[str] = set()
    
    # 1. Extract strings from resources
    results.update(extract_resource_strings(decompile_dir))
    
    # 2. Extract URLs and patterns from smali files
    results.update(extract_patterns_from_smali(decompile_dir))
    
    # 3. Extract hardcoded strings from smali files
    results.update(extract_hardcoded_strings(decompile_dir))
    
    # Convert set to sorted list for consistent output
    return sorted(list(results))

def extract_resource_strings(decompile_dir: str) -> Set[str]:
    """Extract strings from res/values/strings.xml file."""
    strings: Set[str] = set()
    strings_path = os.path.join(decompile_dir, "res", "values", "strings.xml")
    
    if not os.path.isfile(strings_path):
        logger.debug(f"No strings.xml found at {strings_path}")
        return strings
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        for string_elem in root.findall(".//string"):
            if string_elem.text:
                strings.add(string_elem.text.strip())
        
        logger.debug(f"Extracted {len(strings)} strings from resources")
    except Exception as e:
        logger.error(f"Error parsing strings.xml: {e}")
    
    return strings

def extract_patterns_from_smali(decompile_dir: str) -> Set[str]:
    """Extract URLs and sensitive patterns from smali files."""
    patterns: Set[str] = set()
    smali_dir = os.path.join(decompile_dir, "smali")
    
    if not os.path.isdir(smali_dir):
        logger.debug(f"No smali directory found at {smali_dir}")
        return patterns
    
    # Patterns to search for
    regexes = {
        "URL": re.compile(r'"https?://[^\s"\']+'),  # URLs
        "IP": re.compile(r'"(?:\d{1,3}\.){3}\d{1,3}"'),  # IP addresses
        "API_KEY": re.compile(r'"[A-Za-z0-9_-]{20,}"'),  # Possible API keys
        "AWS_KEY": re.compile(r'"[A-Z0-9]{20}"'),  # AWS access keys
        "FIREBASE": re.compile(r'"[A-Za-z0-9_-]{28}\.[A-Za-z0-9_-]{22}"'),  # Firebase URLs
    }
    
    # Walk through all smali files
    for root, _, files in os.walk(smali_dir):
        for file in files:
            if not file.endswith(".smali"):
                continue
            
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for pattern_name, regex in regexes.items():
                        for match in regex.finditer(content):
                            # Clean up the match (remove quotes)
                            value = match.group(0).strip('"')
                            if value:  # Skip empty strings
                                patterns.add(value)
                                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    logger.debug(f"Extracted {len(patterns)} patterns from smali files")
    return patterns

def extract_hardcoded_strings(decompile_dir: str) -> Set[str]:
    """Extract hardcoded strings from smali files."""
    strings: Set[str] = set()
    smali_dir = os.path.join(decompile_dir, "smali")
    
    if not os.path.isdir(smali_dir):
        return strings
    
    # Regex to find const-string instructions in smali
    const_string_pattern = re.compile(r'const-string [^,]+, "([^"\\]*(?:\\.[^"\\]*)*)"')
    
    # Interesting strings to include (minimum length to filter out noise)
    min_length = 8
    
    # Walk through all smali files
    for root, _, files in os.walk(smali_dir):
        for file in files:
            if not file.endswith(".smali"):
                continue
            
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if "const-string" in line:
                            match = const_string_pattern.search(line)
                            if match and len(match.group(1)) >= min_length:
                                # Unescape the string
                                value = match.group(1).encode().decode('unicode_escape')
                                strings.add(value)
                                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    logger.debug(f"Extracted {len(strings)} hardcoded strings from smali files")
    return strings