import sys
import os
import pytest
from unittest.mock import patch, mock_open

# Get the absolute path to the 'src' directory
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

# Add 'src' to sys.path if it's not already there
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from strings_extractor import (
    extract_strings, 
    extract_resource_strings,
    extract_patterns_from_smali,
    extract_hardcoded_strings
)

# Sample strings.xml content for testing
SAMPLE_STRINGS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TestApp</string>
    <string name="welcome_message">Welcome to TestApp!</string>
    <string name="server_url">https://api.example.com</string>
    <string name="empty"></string>
</resources>
"""

# Sample smali file content with URLs and hardcoded strings
SAMPLE_SMALI = """
.class public Lcom/example/testapp/MainActivity;
.super Landroidx/appcompat/app/AppCompatActivity;

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 3
    
    const-string v0, "MainActivity"
    const-string v1, "Application started"
    
    const-string v2, "https://api.example.com/data"
    const-string v3, "apiKey123456789abcdefghijk"
    
    # Some numbers and random strings
    const-string v4, "123"
    const-string v5, "abc"
    
    # IP address
    const-string v6, "192.168.1.1"
    
    # AWS style key
    const-string v7, "AKIAIOSFODNN7EXAMPLE"
    
    return-void
.end method
"""

def mock_file_structure(tmpdir):
    """Create a mock APK structure for testing."""
    # Create directories
    os.makedirs(os.path.join(tmpdir, "res", "values"), exist_ok=True)
    os.makedirs(os.path.join(tmpdir, "smali", "com", "example", "testapp"), exist_ok=True)
    
    # Create strings.xml
    with open(os.path.join(tmpdir, "res", "values", "strings.xml"), "w") as f:
        f.write(SAMPLE_STRINGS_XML)
    
    # Create smali file
    with open(os.path.join(tmpdir, "smali", "com", "example", "testapp", "MainActivity.smali"), "w") as f:
        f.write(SAMPLE_SMALI)
    
    return tmpdir

def test_extract_resource_strings(tmpdir):
    """Test extracting strings from resources."""
    decompile_dir = mock_file_structure(tmpdir)
    
    result = extract_resource_strings(decompile_dir)
    
    assert "TestApp" in result
    assert "Welcome to TestApp!" in result
    assert "https://api.example.com" in result
    assert len(result) == 3  # empty string should be skipped

def test_extract_patterns_from_smali(tmpdir):
    """Test extracting URLs and patterns from smali files."""
    decompile_dir = mock_file_structure(tmpdir)
    
    result = extract_patterns_from_smali(decompile_dir)
    
    assert "https://api.example.com/data" in result
    assert "apiKey123456789abcdefghijk" in result
    assert "192.168.1.1" in result
    assert "AKIAIOSFODNN7EXAMPLE" in result

def test_extract_hardcoded_strings(tmpdir):
    """Test extracting hardcoded strings from smali files."""
    decompile_dir = mock_file_structure(tmpdir)
    
    result = extract_hardcoded_strings(decompile_dir)
    
    # Only strings with length >= 8 should be included
    assert "https://api.example.com/data" in result
    assert "apiKey123456789abcdefghijk" in result
    assert "AKIAIOSFODNN7EXAMPLE" in result
    assert "Application started" in result
    assert "MainActivity" in result  # too short
    assert "123" not in result  # too short
    assert "abc" not in result  # too short

def test_extract_strings_full(tmpdir):
    """Test the full extraction process."""
    decompile_dir = mock_file_structure(tmpdir)
    
    result = extract_strings(decompile_dir)
    
    # Check that results from all sources are combined
    assert "TestApp" in result
    assert "Welcome to TestApp!" in result
    assert "https://api.example.com" in result
    assert "https://api.example.com/data" in result
    assert "apiKey123456789abcdefghijk" in result
    assert "Application started" in result
    assert "AKIAIOSFODNN7EXAMPLE" in result
    assert "192.168.1.1" in result
    
    # Check that duplicates are removed (if any)
    assert len(result) == len(set(result))
    
    # Check that results are sorted
    assert result == sorted(result)