import sys
import os
import pytest

# Ensure src path is included
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from reflection_detector import detect_reflection, extract_class_name, ReflectionInfo
from unpacker import unpack_apk

def test_detect_reflection_empty(tmp_path):
    app_dir = tmp_path / "empty"
    app_dir.mkdir()
    info = detect_reflection(str(app_dir))
    assert isinstance(info, ReflectionInfo)
    assert info.total_issues == 0
    assert not info.has_reflection
    assert not info.has_dynamic_loading
    assert not info.has_native_methods

def test_detect_reflection_flags(tmp_path):
    smali_dir = tmp_path / "smali"
    smali_dir.mkdir()
    (smali_dir / "Test.smali").write_text(
        '.method public static native foo()V\n.end method\n'
        'new-instance v0, Ldalvik/system/DexClassLoader;\n'
        'invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;\n'
    )
    info = detect_reflection(str(tmp_path))
    assert info.has_reflection
    assert info.has_dynamic_loading
    assert info.has_native_methods
    assert info.total_issues == (
        len(info.reflection_calls) + len(info.dynamic_loading) + len(info.native_method_calls)
    )

VALID_APK_PATH = os.path.join("APK", "app_login.apk")

@pytest.mark.skipif(not os.path.isfile(VALID_APK_PATH), reason="APK not found")
def test_reflection_detector_on_real_apk(tmp_path):
    decompiled = unpack_apk(VALID_APK_PATH, out_dir=str(tmp_path / "real_dec"))
    info = detect_reflection(decompiled)

    assert isinstance(info, ReflectionInfo)
    assert isinstance(info.total_issues, int)
    assert hasattr(info, "has_reflection")
    assert hasattr(info, "has_dynamic_loading")
    assert hasattr(info, "has_native_methods")

def test_extract_class_name_simple():
    content = ".class public Lcom/example/MainActivity;"
    assert extract_class_name(content) == "com.example.MainActivity"

def test_extract_class_name_inner_class():
    content = ".class public Lcom/example/MainActivity$Inner;"
    assert extract_class_name(content) == "com.example.MainActivity$Inner"

def test_extract_class_name_missing():
    content = ".super Ljava/lang/Object;"
    assert extract_class_name(content) == "Unknown"

def test_extract_class_name_with_flags():
    content = ".class public abstract interface Lorg/example/MyInterface;"
    assert extract_class_name(content) == "org.example.MyInterface"
