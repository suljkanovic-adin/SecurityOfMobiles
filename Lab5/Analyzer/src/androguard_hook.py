# androguard_hook.py

import os
import logging
from typing import List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class AndroguardData:
    package_name: str
    main_activity: str
    min_sdk: int
    target_sdk: int
    permissions: List[str] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    receivers: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    dangerous_permissions: List[str] = field(default_factory=list)

    @property
    def total_components(self) -> int:
        return len(self.activities) + len(self.services) + len(self.receivers) + len(self.providers)

def is_androguard_available() -> bool:
    try:
        import androguard  # noqa: F401
        return True
    except ImportError:
        return False

def analyze_apk(apk_path: str) -> AndroguardData:
    if not os.path.isfile(apk_path):
        raise ValueError(f"APK file not found: {apk_path}")

    try:
        from androguard.core.apk import APK
    except ImportError:
        logger.error("Androguard is not installed.")
        raise ImportError("Androguard is not installed. Use: pip install androguard")

    try:
        apk = APK(apk_path)

        # Extract fields
        package_name = apk.get_package()
        main_activity = apk.get_main_activity() or ""
        min_sdk = int(apk.get_min_sdk_version() or 0)
        target_sdk = int(apk.get_target_sdk_version() or 0)
        permissions = apk.get_permissions()
        activities = apk.get_activities()
        services = apk.get_services()
        receivers = apk.get_receivers()
        providers = apk.get_providers()

        # Dangerous permissions
        keywords = ("sms", "call", "location", "contact")
        dangerous_permissions = [p for p in permissions if any(k in p.lower() for k in keywords)]

        return AndroguardData(
            package_name=package_name,
            main_activity=main_activity,
            min_sdk=min_sdk,
            target_sdk=target_sdk,
            permissions=permissions,
            activities=activities,
            services=services,
            receivers=receivers,
            providers=providers,
            dangerous_permissions=dangerous_permissions
        )

    except Exception as e:
        logger.error(f"Failed to analyze APK: {e}")
        raise ValueError(f"Failed to analyze APK with Androguard: {e}")