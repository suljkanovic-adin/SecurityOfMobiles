import sys
import os
import pytest

# Ensure src path is included
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from native_detector import list_native_libs, analyze_native_function_usage, NativeLibInfo
from unpacker import unpack_apk

def test_list_native_libs_empty(tmp_path):
    """Should return an empty list if lib/ folder is missing."""
    empty_app = tmp_path / "no_libs"
    empty_app.mkdir()
    assert list_native_libs(str(empty_app)) == []

def test_list_native_libs_detects_arch(tmp_path):
    app_dir = tmp_path / "my_app"
    lib_dir = app_dir / "lib" / "armeabi-v7a"
    lib_dir.mkdir(parents=True)
    (lib_dir / "foo.so").write_bytes(b"binary")
    results = list_native_libs(str(app_dir))
    assert len(results) == 1
    assert results[0].architecture == "armeabi-v7a"
    assert results[0].name == "foo.so"

def test_analyze_native_usage_no_libs(tmp_path):
    app_dir = tmp_path / "project"
    app_dir.mkdir()
    usage = analyze_native_function_usage(str(app_dir))
    assert usage == {}

def test_analyze_native_usage_detect(tmp_path):
    app_dir = tmp_path / "app"
    lib_dir = app_dir / "lib" / "armeabi-v7a"
    lib_dir.mkdir(parents=True)
    (lib_dir / "bar.so").write_bytes(b"binary")
    smali_dir = app_dir / "smali"
    smali_dir.mkdir()
    (smali_dir / "Example.smali").write_text(
        'const-string v0, "bar"\n'
        'invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n'
    )
    usage = analyze_native_function_usage(str(app_dir))
    assert usage.get("bar.so") == 1

VALID_APK_PATH = os.path.join("APK", "app_login.apk")

@pytest.mark.skipif(not os.path.isfile(VALID_APK_PATH), reason="APK not found")
def test_native_detector_on_real_apk(tmp_path):
    decompiled = unpack_apk(VALID_APK_PATH, out_dir=str(tmp_path / "real_app"))
    libs = list_native_libs(decompiled)
    usage = analyze_native_function_usage(decompiled)

    assert isinstance(libs, list)
    assert isinstance(usage, dict)
    for lib in libs:
        assert isinstance(lib, NativeLibInfo)
        assert lib.name.endswith(".so")
