import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from lxml import etree

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class Permission:
    """Represents an Android permission."""
    name: str
    protection_level: Optional[str] = None
    
@dataclass
class Component:
    """Represents an Android component (Activity, Service, etc.)."""
    name: str
    type: str  # "activity", "service", "receiver", "provider"
    exported: bool = False
    permission: Optional[str] = None
    intent_filters: List[Dict[str, List[str]]] = None
    
    def __post_init__(self):
        if self.intent_filters is None:
            self.intent_filters = []

@dataclass
class ManifestData:
    """Container for parsed Android manifest data."""
    package_name: str
    version_code: int
    version_name: str
    min_sdk: int
    target_sdk: int
    permissions: List[Permission]
    components: List[Component]
    debuggable: bool = False
    allow_backup: bool = True
    custom_attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_attributes is None:
            self.custom_attributes = {}

def parse_manifest(decompile_dir: str) -> ManifestData:
    """
    Parse the AndroidManifest.xml file in the decompiled directory.
    
    Args:
        decompile_dir: Path to the decompiled APK directory
        
    Returns:
        ManifestData object containing the parsed manifest information
        
    Raises:
        FileNotFoundError: If AndroidManifest.xml is not found
        ValueError: If manifest parsing fails
    """
    manifest_path = os.path.join(decompile_dir, "AndroidManifest.xml")
    
    if not os.path.isfile(manifest_path):
        logger.error(f"AndroidManifest.xml not found at {manifest_path}")
        raise FileNotFoundError(f"AndroidManifest.xml not found at {manifest_path}")
    
    try:
        # Parse the XML
        logger.info(f"Parsing AndroidManifest.xml at {manifest_path}")
        tree = etree.parse(manifest_path)
        root = tree.getroot()
        
        # Define namespaces
        ns = {
            'android': 'http://schemas.android.com/apk/res/android',
        }
        
        # Extract basic app info
        package_name = root.get('package')
        if not package_name:
            raise ValueError("Missing package name in manifest")
        
        # Default values
        version_code = 0
        version_name = ""
        min_sdk = 0
        target_sdk = 0
        debuggable = False
        allow_backup = True
        custom_attributes = {}
        
        # Extract application attributes
        app_node = root.find(".//application")
        if app_node is not None:
            debuggable_attr = app_node.get(f"{{{ns['android']}}}debuggable")
            backup_attr = app_node.get(f"{{{ns['android']}}}allowBackup")
            
            debuggable = debuggable_attr == "true" if debuggable_attr else False
            allow_backup = backup_attr != "false" if backup_attr else True
            
            # Store any other interesting application attributes
            for key, value in app_node.attrib.items():
                if key not in [f"{{{ns['android']}}}debuggable", f"{{{ns['android']}}}allowBackup"]:
                    custom_attributes[key.replace(f"{{{ns['android']}}}", "")] = value
        
        # Extract version info
        version_code_attr = root.get(f"{{{ns['android']}}}versionCode")
        version_name_attr = root.get(f"{{{ns['android']}}}versionName")
        
        if version_code_attr:
            version_code = int(version_code_attr)
        if version_name_attr:
            version_name = version_name_attr
        
        # Extract SDK info from uses-sdk
        sdk_node = root.find(".//uses-sdk")
        if sdk_node is not None:
            min_sdk_attr = sdk_node.get(f"{{{ns['android']}}}minSdkVersion")
            target_sdk_attr = sdk_node.get(f"{{{ns['android']}}}targetSdkVersion")
            
            if min_sdk_attr:
                min_sdk = int(min_sdk_attr)
            if target_sdk_attr:
                target_sdk = int(target_sdk_attr)
        
        # Extract permissions
        permissions = []
        for perm_node in root.findall(".//uses-permission"):
            perm_name = perm_node.get(f"{{{ns['android']}}}name")
            if perm_name:
                permissions.append(Permission(name=perm_name))
        
        # Extract permission definitions
        for perm_def_node in root.findall(".//permission"):
            perm_name = perm_def_node.get(f"{{{ns['android']}}}name")
            protection_level = perm_def_node.get(f"{{{ns['android']}}}protectionLevel")
            if perm_name:
                permissions.append(Permission(
                    name=perm_name, 
                    protection_level=protection_level
                ))
        
        # Extract components
        components = []
        
        # Helper function to parse components
        def parse_components(nodes, component_type):
            for node in nodes:
                name = node.get(f"{{{ns['android']}}}name")
                if not name:
                    continue
                    
                # Normalize name (add package prefix if needed)
                if name.startswith("."):
                    name = package_name + name
                elif "." not in name:
                    name = f"{package_name}.{name}"
                
                # Check if exported
                exported_attr = node.get(f"{{{ns['android']}}}exported")
                has_intent_filters = len(node.findall(".//intent-filter")) > 0
                
                # By default, components with intent filters are exported
                exported = False
                if exported_attr is not None:
                    exported = exported_attr == "true"
                elif has_intent_filters:
                    exported = True
                
                # Get permission
                permission = node.get(f"{{{ns['android']}}}permission")
                
                # Parse intent filters
                intent_filters = []
                for filter_node in node.findall(".//intent-filter"):
                    intent_filter = {"actions": [], "categories": [], "data": []}
                    
                    # Get actions
                    for action in filter_node.findall(".//action"):
                        action_name = action.get(f"{{{ns['android']}}}name")
                        if action_name:
                            intent_filter["actions"].append(action_name)
                    
                    # Get categories
                    for category in filter_node.findall(".//category"):
                        category_name = category.get(f"{{{ns['android']}}}name")
                        if category_name:
                            intent_filter["categories"].append(category_name)
                    
                    # Get data (simplified - just get scheme)
                    for data in filter_node.findall(".//data"):
                        scheme = data.get(f"{{{ns['android']}}}scheme")
                        if scheme:
                            intent_filter["data"].append(f"scheme:{scheme}")
                    
                    intent_filters.append(intent_filter)
                
                components.append(Component(
                    name=name,
                    type=component_type,
                    exported=exported,
                    permission=permission,
                    intent_filters=intent_filters
                ))
        
        # Parse each component type
        parse_components(root.findall(".//activity"), "activity")
        parse_components(root.findall(".//service"), "service")
        parse_components(root.findall(".//receiver"), "receiver")
        parse_components(root.findall(".//provider"), "provider")
        
        # Create and return the manifest data
        return ManifestData(
            package_name=package_name,
            version_code=version_code,
            version_name=version_name,
            min_sdk=min_sdk,
            target_sdk=target_sdk,
            permissions=permissions,
            components=components,
            debuggable=debuggable,
            allow_backup=allow_backup,
            custom_attributes=custom_attributes
        )
        
    except etree.XMLSyntaxError as e:
        logger.error(f"XML parsing error: {e}")
        raise ValueError(f"Failed to parse manifest XML: {e}")
    except Exception as e:
        logger.error(f"Error parsing manifest: {e}")
        raise ValueError(f"Error parsing manifest: {e}")