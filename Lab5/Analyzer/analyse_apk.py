import os
import sys
import json
import logging
import shutil
import tempfile
from datetime import datetime

# --- Get the Base Directory ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Construct Paths relative to BASE_DIR ---
SRC_DIR = os.path.join(BASE_DIR, 'src')
APK_DIR = os.path.join(BASE_DIR, 'APK')
REPORTS_DIR = os.path.join(BASE_DIR, 'analysis_reports')

# --- Add 'src' directory to Python's search path ---
# This allows importing modules directly from the 'src' folder
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- Import your analysis functions (from 'src' directory) ---
try:
    from unpacker import unpack_apk, UnpackError
    from manifest_parser import parse_manifest
    from androguard_hook import analyze_apk as analyze_with_androguard, is_androguard_available
    from native_detector import list_native_libs, analyze_native_function_usage
    from reflection_detector import detect_reflection
    from strings_extractor import extract_strings
except ImportError as e:
    print(f"Error importing analysis modules from '{SRC_DIR}': {e}")
    print("Ensure all required .py files are present in the 'src' directory and dependencies are installed.")
    sys.exit(1)

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
os.makedirs(REPORTS_DIR, exist_ok=True) # Ensure reports directory exists

# --- Main Analysis Function (No changes needed inside) ---
def run_analysis(apk_path):
    """Runs all analysis steps for a given APK."""
    if not os.path.isfile(apk_path):
        logging.error(f"APK file not found: {apk_path}")
        return None

    apk_filename = os.path.basename(apk_path)
    report = {"apk_file": apk_filename, "analysis_timestamp": datetime.now().isoformat()}
    decompile_dir = None

    try:
        # 1. Unpack APK using apktool
        logging.info(f"Unpacking {apk_filename}...")
        temp_base = os.path.splitext(apk_filename)[0] + "_decompiled"
        decompile_dir = os.path.join(tempfile.gettempdir(), temp_base + "_" + str(os.getpid()))
        if os.path.exists(decompile_dir):
             shutil.rmtree(decompile_dir)

        unpack_apk(apk_path, out_dir=decompile_dir)
        logging.info(f"APK decompiled to temporary directory: {decompile_dir}")

        # 2. Parse Manifest (from decompiled dir)
        logging.info("Parsing AndroidManifest.xml...")
        try:
            manifest_data = parse_manifest(decompile_dir)
            # Convert dataclasses/namedtuples to dicts for JSON serialization
            report["manifest_info"] = manifest_data.__dict__
            report["manifest_info"]["components"] = [comp.__dict__ for comp in manifest_data.components]
            report["manifest_info"]["permissions"] = [perm.__dict__ for perm in manifest_data.permissions]
        except Exception as e:
            logging.error(f"Manifest parsing failed: {e}")
            report["manifest_info"] = {"error": str(e)}

        # 3. Detect Native Libs (from decompiled dir)
        logging.info("Detecting native libraries...")
        try:
            native_libs = list_native_libs(decompile_dir)
            report["native_libraries"] = [lib._asdict() for lib in native_libs] # Use _asdict() for NamedTuple
            lib_usage = analyze_native_function_usage(decompile_dir)
            report["native_library_usage"] = lib_usage
        except Exception as e:
            logging.error(f"Native library detection failed: {e}")
            report["native_libraries"] = {"error": str(e)}

        # 4. Detect Reflection/Dynamic Loading (from decompiled dir)
        logging.info("Detecting reflection and dynamic loading...")
        try:
            reflection_data = detect_reflection(decompile_dir)
            report["reflection_dynamic_loading"] = reflection_data.__dict__
        except Exception as e:
            logging.error(f"Reflection detection failed: {e}")
            report["reflection_dynamic_loading"] = {"error": str(e)}

        # 5. Extract Strings (from decompiled dir)
        logging.info("Extracting strings...")
        try:
            interesting_strings = extract_strings(decompile_dir)
            report["interesting_strings"] = interesting_strings
        except Exception as e:
            logging.error(f"String extraction failed: {e}")
            report["interesting_strings"] = {"error": str(e)}

        # 6. Analyze with Androguard (optional, on original APK)
        if is_androguard_available():
            logging.info("Analyzing with Androguard...")
            try:
                androguard_data = analyze_with_androguard(apk_path)
                report["androguard_info"] = androguard_data.__dict__
            except Exception as e:
                logging.error(f"Androguard analysis failed: {e}")
                report["androguard_info"] = {"error": str(e)}
        else:
            logging.warning("Androguard not available, skipping Androguard analysis.")
            report["androguard_info"] = {"status": "Skipped (Androguard not installed)"}

    except UnpackError as e:
        logging.error(f"Failed to unpack {apk_filename}: {e}")
        report["error"] = f"Unpacking failed: {e}"
    except Exception as e:
        logging.exception(f"An unexpected error occurred during analysis for {apk_filename}") # Log stack trace
        report["error"] = f"Unexpected analysis error: {e}"
    finally:
        # Clean up the decompiled directory
        if decompile_dir and os.path.exists(decompile_dir):
            logging.info(f"Cleaning up temporary directory: {decompile_dir}")
            try:
                shutil.rmtree(decompile_dir)
            except Exception as e:
                logging.error(f"Failed to remove temporary directory {decompile_dir}: {e}")

    return report

# --- Report Generation Function (No changes needed inside) ---
def format_report(report_data, output_format="txt"):
    """Formats the analysis data into a human-readable report."""
    if not report_data:
        return "Analysis failed, no data to report."

    lines = []
    apk_file = report_data.get('apk_file', 'Unknown APK')
    lines.append(f"Analysis Report for: {apk_file}")
    lines.append(f"Analysis Time: {report_data.get('analysis_timestamp', 'N/A')}")
    lines.append("=" * 40)

    if "error" in report_data:
        lines.append(f"!!! ANALYSIS ERROR: {report_data['error']} !!!")
        lines.append("Check logs for more details.")
        lines.append("=" * 40)
        # Still try to print partial results if available
        # return "\n".join(lines) # Option: return early on fatal error

    # Manifest Info
    manifest = report_data.get('manifest_info', {})
    lines.append("\n--- Manifest Information ---")
    if manifest and isinstance(manifest, dict) and not manifest.get("error"):
        lines.append(f"Package Name: {manifest.get('package_name', 'N/A')}")

        main_activity_name = 'Not Found'
        manifest_components = manifest.get('components', [])
        if manifest_components:
            for c in manifest_components:
                if c.get('type') == 'activity':
                    for intent_filter in c.get('intent_filters', []):
                        # Ensure actions/categories are lists before checking 'in'
                        actions = intent_filter.get('actions', [])
                        categories = intent_filter.get('categories', [])
                        if isinstance(actions, list) and isinstance(categories, list):
                           has_main = 'android.intent.action.MAIN' in actions
                           has_launcher = 'android.intent.category.LAUNCHER' in categories
                           if has_main and has_launcher:
                               main_activity_name = c.get('name', 'N/A')
                               break
                if main_activity_name != 'Not Found':
                    break

        lines.append(f"Main Activity: {main_activity_name}")
        lines.append(f"Min SDK: {manifest.get('min_sdk', 'N/A')}")
        lines.append(f"Target SDK: {manifest.get('target_sdk', 'N/A')}")
        lines.append(f"Debuggable: {manifest.get('debuggable', 'N/A')}")
        lines.append(f"Allow Backup: {manifest.get('allow_backup', 'N/A')}")

        lines.append("\nPermissions:")
        perms = manifest.get('permissions', [])
        if perms:
            for p in perms:
                lines.append(f"- {p.get('name', 'N/A')}" + (f" (Protection: {p['protection_level']})" if p.get('protection_level') else ""))
        else:
            lines.append("  None found.")

        lines.append("\nComponents:")
        comps = manifest.get('components', [])
        if comps:
            for comp_type in ["activity", "service", "receiver", "provider"]:
                type_comps = [c for c in comps if c.get('type') == comp_type]
                if type_comps:
                    lines.append(f"  {comp_type.capitalize()}s:")
                    for c in type_comps:
                        lines.append(f"  - {c.get('name', 'N/A')}" + (" (Exported)" if c.get('exported') else ""))
        else:
            lines.append("  None found.")

    elif manifest.get("error"):
         lines.append(f"Error during Manifest parsing: {manifest['error']}")
    else:
        lines.append("  No manifest data available.")


    # Native Libraries
    native = report_data.get('native_libraries', {})
    lines.append("\n--- Native Libraries ---")
    if isinstance(native, list) and native:
         for lib in native:
             lines.append(f"- {lib.get('path', 'N/A')} (Arch: {lib.get('architecture', 'N/A')})")
         usage = report_data.get('native_library_usage', {})
         lines.append("\n  Usage Counts (System.loadLibrary):")
         # Ensure usage is a dict before iterating
         used_libs = {k:v for k,v in usage.items() if isinstance(usage, dict) and v > 0}
         if used_libs:
              for lib_name, count in used_libs.items():
                   lines.append(f"  - {lib_name}: {count} calls")
         else:
              lines.append("    None detected.")
    elif isinstance(native, dict) and native.get("error"):
         lines.append(f"Error during Native Library detection: {native['error']}")
    else:
         lines.append("  None found or detection failed.")


    # Reflection & Dynamic Loading
    reflect = report_data.get('reflection_dynamic_loading', {})
    lines.append("\n--- Reflection & Dynamic Loading ---")
    if reflect and isinstance(reflect, dict) and not reflect.get("error"):
        lines.append(f"Reflection Calls Found: {len(reflect.get('reflection_calls', [])) > 0}")
        lines.append(f"Dynamic Loading Found: {len(reflect.get('dynamic_loading', [])) > 0}")
        lines.append(f"Native Method Calls/Loads Found: {len(reflect.get('native_method_calls', [])) > 0}")
        # Optional: Add details here if needed, similar to previous versions
    elif reflect.get("error"):
         lines.append(f"Error during Reflection/Dynamic Loading detection: {reflect['error']}")
    else:
         lines.append("  Detection not run or failed.")


    # Interesting Strings
    strings = report_data.get('interesting_strings', [])
    lines.append("\n--- Interesting Strings ---")
    if isinstance(strings, list) and strings:
         limit = 50
         for s in strings[:limit]:
             lines.append(f"- {s}")
         if len(strings) > limit:
             lines.append(f"... and {len(strings) - limit} more.")
    elif isinstance(strings, dict) and strings.get("error"): # Check if it's an error dict
         lines.append(f"Error during String Extraction: {strings['error']}")
    elif not strings: # Check if list is empty
         lines.append("  None found.")
    else: # Handle unexpected type
         lines.append("  String extraction data unavailable or in unexpected format.")

    # Optional: Androguard Info Summary
    ag_info = report_data.get('androguard_info', {})
    lines.append("\n--- Androguard Summary (Optional) ---")
    if ag_info and isinstance(ag_info, dict) and not ag_info.get("error") and ag_info.get("status") != "Skipped (Androguard not installed)":
        lines.append(f"Package: {ag_info.get('package_name', 'N/A')}")
        lines.append(f"Main Activity (from Androguard): {ag_info.get('main_activity', 'N/A')}")
        lines.append("Dangerous Permissions Found:")
        dang_perms = ag_info.get('dangerous_permissions', [])
        if dang_perms:
            for p in dang_perms: lines.append(f"- {p}")
        else:
            lines.append("  None identified by keyword search.")
    elif ag_info.get("error"):
         lines.append(f"Error during Androguard analysis: {ag_info['error']}")
    elif ag_info.get("status") == "Skipped (Androguard not installed)":
        lines.append("  Skipped (Androguard library not installed or found).")
    else:
         lines.append("  No Androguard data available.")


    return "\n".join(lines)


# --- Script Execution ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        # Updated usage message
        print(f"Usage: python {os.path.basename(__file__)} <apk_filename>")
        print(f"       (Run this script from the '{os.path.basename(BASE_DIR)}' directory)")
        print(f"       (Place the APK file inside the '{os.path.basename(APK_DIR)}/' subdirectory)")
        print(f"       (Reports will be saved in the '{os.path.basename(REPORTS_DIR)}/' subdirectory)")

        # List available APKs in the correct directory
        print("\nAvailable APKs:")
        try:
            # Check if APK_DIR exists before listing
            if os.path.isdir(APK_DIR):
                apks = [f for f in os.listdir(APK_DIR) if f.endswith(".apk")]
                if apks:
                    for apk_f in apks: print(f"- {apk_f}")
                else:
                    print(f"  No .apk files found in '{APK_DIR}'.")
            else:
                 print(f"  Error: APK directory '{APK_DIR}' not found.")
        except Exception as e:
            print(f"  Error listing APKs: {e}")
        sys.exit(1)

    target_apk_name = sys.argv[1]
    # Construct the full path to the target APK inside the APK_DIR
    target_apk_path = os.path.join(APK_DIR, target_apk_name)

    # Check if the target APK exists before running analysis
    if not os.path.isfile(target_apk_path):
        logging.error(f"Target APK not found: {target_apk_path}")
        print(f"Error: The specified APK file '{target_apk_name}' was not found in the '{APK_DIR}' directory.")
        sys.exit(1)

    # Run the main analysis pipeline
    analysis_results = run_analysis(target_apk_path)

    # Process results and generate reports
    if analysis_results:
        report_filename_base = os.path.splitext(target_apk_name)[0]
        # Construct full paths for report files inside REPORTS_DIR
        report_txt_path = os.path.join(REPORTS_DIR, f"{report_filename_base}_report.txt")
        report_json_path = os.path.join(REPORTS_DIR, f"{report_filename_base}_report.json")

        # Write the text report
        report_text = format_report(analysis_results)
        try:
            with open(report_txt_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            logging.info(f"Text report saved to: {report_txt_path}")
        except IOError as e:
            logging.error(f"Failed to write text report file: {e}")

        # Write the JSON data
        try:
            with open(report_json_path, "w", encoding="utf-8") as f:
                # Use default=str to handle potential non-serializable types like dataclasses if conversion failed
                json.dump(analysis_results, f, indent=2, default=str)
            logging.info(f"JSON data saved to: {report_json_path}")
        except IOError as e:
            logging.error(f"Failed to write JSON report file: {e}")
        except TypeError as e:
             logging.error(f"Failed to serialize results to JSON: {e}. Check data structures.")

    else:
        logging.error("Analysis failed or produced no results. No report generated.")
        print("Analysis failed. Please check the logs for errors.")