import sys
import os
import pytest
from unittest.mock import patch
from lxml import etree

# Ensure 'src' is on the import path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from manifest_parser import parse_manifest, ManifestData, Permission, Component

SAMPLE_MANIFEST = """<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.testapp"
    android:versionCode="10"
    android:versionName="1.0">
    
    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="30" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <permission android:name="com.example.testapp.CUSTOM_PERMISSION" android:protectionLevel="signature" />
    
    <application android:allowBackup="true" android:debuggable="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <service android:name=".BackgroundService" android:exported="false" />
        <receiver android:name="com.example.testapp.BootReceiver"
                  android:permission="android.permission.RECEIVE_BOOT_COMPLETED">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
        <provider android:name=".DataProvider"
                  android:authorities="com.example.testapp.provider"
                  android:exported="true"
                  android:permission="com.example.testapp.CUSTOM_PERMISSION" />
    </application>
</manifest>
"""

def test_manifest_not_found():
    """Raise FileNotFoundError if manifest path is invalid."""
    with pytest.raises(FileNotFoundError):
        parse_manifest("/non/existent/path")

def test_parse_mocked_manifest():
    """Test parsing a fake manifest via patching."""
    with patch("os.path.isfile", return_value=True), \
         patch("lxml.etree.parse") as mock_parse:

        root = etree.fromstring(SAMPLE_MANIFEST, parser=etree.XMLParser())
        mock_tree = mock_parse.return_value
        mock_tree.getroot.return_value = root

        result = parse_manifest("/fake/path")
        assert isinstance(result, ManifestData)
        assert result.package_name == "com.example.testapp"
        assert result.version_code == 10
        assert result.version_name == "1.0"
        assert result.min_sdk == 21
        assert result.target_sdk == 30
        assert result.debuggable is True
        assert result.allow_backup is True
        assert len(result.permissions) == 3
        assert any(p.name == "android.permission.INTERNET" for p in result.permissions)
        assert any(p.name == "android.permission.ACCESS_NETWORK_STATE" for p in result.permissions)
        assert any(p.protection_level == "signature" for p in result.permissions if "CUSTOM_PERMISSION" in p.name)

        components = result.components
        assert any(c.type == "activity" and "MainActivity" in c.name for c in components)
        assert any(c.type == "service" and "BackgroundService" in c.name for c in components)
        assert any(c.type == "receiver" and "BootReceiver" in c.name for c in components)
        assert any(c.type == "provider" and "DataProvider" in c.name for c in components)

VALID_APK_PATH = os.path.join("APK", "app_login.apk")

@pytest.mark.skipif(not os.path.isfile(VALID_APK_PATH), reason="Real APK not found.")
def test_parse_manifest_from_real_apk(tmp_path):
    """
    This test runs on a real APK, decompiles it, and parses the actual AndroidManifest.xml.
    """
    from unpacker import unpack_apk  # import only when needed

    decompiled = unpack_apk(VALID_APK_PATH, out_dir=str(tmp_path / "decompiled"))
    result = parse_manifest(decompiled)

    assert isinstance(result, ManifestData)
    assert isinstance(result.package_name, str)
    assert isinstance(result.permissions, list)
    assert isinstance(result.components, list)
    assert os.path.basename(decompiled) == "decompiled"
