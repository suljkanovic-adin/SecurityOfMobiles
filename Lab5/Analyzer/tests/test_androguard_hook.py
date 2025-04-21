import os
import sys
import pytest

# add src path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from androguard_hook import analyze_apk, is_androguard_available, AndroguardData

def test_is_androguard_available():
    assert is_androguard_available() is True

def test_analyze_apk_nonexistent(tmp_path):
    fake_apk = tmp_path / "nope.apk"
    with pytest.raises(ValueError) as e:
        analyze_apk(str(fake_apk))
    assert "APK file not found" in str(e.value)

def test_analyze_apk_invalid_apk(tmp_path):
    invalid_apk = tmp_path / "invalid.apk"
    invalid_apk.write_bytes(b"not an apk")
    with pytest.raises(ValueError) as e:
        analyze_apk(str(invalid_apk))
    assert "Failed to analyze APK" in str(e.value)

# You must update this path to point to a real .apk on your system
VALID_APK_PATH = os.getenv("REAL_APK_PATH", os.path.join("APK", "app_login.apk"))

@pytest.mark.skipif(not os.path.isfile(VALID_APK_PATH), reason="Valid test APK not set")
def test_analyze_apk_valid():
    data = analyze_apk(VALID_APK_PATH)
    assert isinstance(data, AndroguardData)
    assert data.package_name != ""
    assert isinstance(data.activities, list)
    assert isinstance(data.permissions, list)