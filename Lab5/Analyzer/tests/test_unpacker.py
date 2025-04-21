# tests/test_unpacker.py

import sys
import os

# Get the absolute path to the 'src' directory
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

# Add 'src' to sys.path if it's not already there
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from unpacker import unpack_apk, UnpackError

def test_unpack_invalid_apk_raises(tmp_path):
    """
    Given a path to an invalid or empty file,
    unpack_apk should raise UnpackError.
    """
    # Create a dummy APK file with no content
    dummy_apk = tmp_path / "dummy.apk"
    dummy_apk.write_bytes(b"")  # invalid APK structure
    with pytest.raises(UnpackError):
        unpack_apk(str(dummy_apk))


def test_unpack_valid_apk_creates_dir(tmp_path):
    """
    Given a valid APK, unpack_apk should produce a folder
    containing AndroidManifest.xml and return its path.
    """
    # Set this to a valid APK on your system, or export REAL_APK_PATH
    VALID_APK_PATH = os.getenv("REAL_APK_PATH", os.path.join("APK", "app_login.apk"))
    assert os.path.isfile(VALID_APK_PATH), f"Please set a valid APK path at {VALID_APK_PATH}"

    # Use tmp_path as the base output directory
    out_dir = tmp_path / "decompiled"
    result_dir = unpack_apk(VALID_APK_PATH, out_dir=str(out_dir))

    # Check that unpack_apk returned the correct directory
    assert os.path.isdir(result_dir), f"Decompile directory {result_dir} does not exist"
    
    # Check that AndroidManifest.xml is present
    manifest_path = os.path.join(result_dir, "AndroidManifest.xml")
    assert os.path.isfile(manifest_path), "AndroidManifest.xml was not found in the decompiled output"
