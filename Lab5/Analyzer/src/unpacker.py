# unpacker.py

import subprocess
import shutil
import os
import tempfile
from typing import Optional

class UnpackError(Exception):
    """Raised when APK unpacking fails."""
    pass

def unpack_apk(apk_path: str, out_dir: Optional[str] = None) -> str:
    """
    Decompile the given APK into a temporary folder using apktool.
    Returns the path to the decompiled directory.
    Raises UnpackError on any failure.
    """
    # 1) Locate the apktool executable (handles Unix 'apktool' and Windows 'apktool.bat')
    apktool_cmd = shutil.which("apktool") or shutil.which("apktool.bat")
    if not apktool_cmd:
        raise UnpackError(
            "apktool executable not found. Please install apktool and add it to your PATH."
        )

    # 2) Determine output directory
    if out_dir is None:
        base = os.path.splitext(os.path.basename(apk_path))[0]
        # Use system temp directory instead of hardcoded "tmp"
        out_dir = os.path.join(tempfile.gettempdir(), base)

    # 3) Clean up any existing directory
    if os.path.isdir(out_dir):
        try:
            shutil.rmtree(out_dir)
        except (PermissionError, OSError) as e:
            raise UnpackError(f"Cannot clean output directory: {e}")

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)

    # 4) Build and run the apktool command
    # IMPORTANT: Don't use shell=True on Windows to avoid the "press any key" prompt
    # Instead, pass input="" to automatically handle prompts
    try:
        # For Windows, use this approach which provides empty input to bypass the prompt
        cmd = [apktool_cmd, "d", "-f", "-o", out_dir, apk_path]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            # Using shell=False to avoid Windows command processor
            shell=False,
        )
        
        # Provide empty input and set a reasonable timeout (180 seconds)
        stdout, stderr = process.communicate(input=b"\n", timeout=180)
        
        # Check for failure
        if process.returncode != 0:
            stderr_text = stderr.decode(errors="ignore").strip()
            raise UnpackError(f"apktool failed with code {process.returncode}: {stderr_text}")
            
    except subprocess.TimeoutExpired:
        # Make sure to kill the process if it times out
        process.kill()
        raise UnpackError("apktool timed out after 180 seconds")
    except Exception as e:
        # Catch FileNotFoundError or other OS errors
        raise UnpackError(f"Failed to invoke apktool: {e}")

    # 5) Validate that AndroidManifest.xml exists in the output
    manifest_path = os.path.join(out_dir, "AndroidManifest.xml")
    if not os.path.isfile(manifest_path):
        raise UnpackError(f"Missing AndroidManifest.xml in {out_dir}")

    return out_dir