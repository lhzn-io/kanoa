"""
Authentication and environment helpers for kanoa.

Inspired by the gemini-mode bash function, this module provides utilities
for managing Google AI authentication (AI Studio vs Vertex AI) and
automatically detecting gcloud configuration.
"""

import json
import os
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

# Config file location
KANOA_CONFIG_DIR = Path.home() / ".kanoa"
KANOA_CONFIG_FILE = KANOA_CONFIG_DIR / "config"
KANOA_ENV_FILE = KANOA_CONFIG_DIR / "env"


def update_session_env(env_vars: Dict[str, str]) -> None:
    """
    Write environment variables to a shell-sourceable file.
    """
    KANOA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f'export {k}="{v}"' for k, v in env_vars.items()]
    KANOA_ENV_FILE.write_text("\n".join(lines) + "\n")


def run_gcloud_command(args: list[str]) -> Tuple[bool, str]:
    """
    Run a gcloud command and return success status and output.

    Args:
        args: List of gcloud command arguments (e.g., ['config', 'get', 'project'])

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ["gcloud", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


# Cache for gcloud configuration
_GCLOUD_CONFIG_CACHE: Optional[Dict[str, str]] = None


def get_gcloud_config_programmatic() -> Dict[str, str]:
    """
    Attempt to read gcloud config directly from files to avoid slow CLI overhead.
    """
    config: Dict[str, str] = {}
    gcloud_config_path = Path.home() / ".config" / "gcloud"
    active_config_file = gcloud_config_path / "active_config"

    if not active_config_file.exists():
        return config

    try:
        active_config = active_config_file.read_text().strip()
        config_file = gcloud_config_path / "configurations" / f"config_{active_config}"

        if config_file.exists():
            import configparser

            cp = configparser.ConfigParser()
            cp.read(config_file)

            if "core" in cp and "project" in cp["core"]:
                config["project"] = cp["core"]["project"]
            if "compute" in cp:
                if "region" in cp["compute"]:
                    config["region"] = cp["compute"]["region"]
                if "zone" in cp["compute"]:
                    config["zone"] = cp["compute"]["zone"]
    except Exception:
        pass

    return config


def get_gcloud_config() -> Dict[str, str]:
    """
    Get current gcloud configuration (project, region, zone).
    Caches the result for the duration of the process.
    """
    global _GCLOUD_CONFIG_CACHE
    if _GCLOUD_CONFIG_CACHE is not None:
        return _GCLOUD_CONFIG_CACHE

    # 1. Try programmatic first (fastest)
    config = get_gcloud_config_programmatic()

    # 2. Fallback to CLI if essential info missing
    if not config.get("project"):
        success, output = run_gcloud_command(["config", "list", "--format", "json"])
        if success and output:
            with suppress(Exception):
                data = json.loads(output)
                config["project"] = data.get("core", {}).get("project", "")
                config["region"] = data.get("compute", {}).get("region", "")
                config["zone"] = data.get("compute", {}).get("zone", "")

    # 3. Last resort fallback for project
    if not config.get("project"):
        _, p = run_gcloud_command(["config", "get-value", "project", "--quiet"])
        if p:
            config["project"] = p

    _GCLOUD_CONFIG_CACHE = config
    return config


def get_gcloud_project() -> Optional[str]:
    """
    Get the current gcloud project ID from configuration.
    """
    return get_gcloud_config().get("project")


def get_gcloud_location() -> Optional[str]:
    """
    Get the current gcloud region from configuration.
    """
    return get_gcloud_config().get("region")


def check_adc_status() -> bool:
    """
    Check if Application Default Credentials (ADC) are configured.

    Returns:
        True if ADC is configured, False otherwise.
    """
    # 1. Check environment variable
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        env_path = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
        if env_path.exists():
            return True

    # 2. Check for default ADC file
    adc_path = (
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )
    if adc_path.exists():
        return True

    # Try to run a simple auth check
    success, _ = run_gcloud_command(
        ["auth", "application-default", "print-access-token"]
    )
    return success


def get_api_key_paths() -> Dict[str, Optional[Path]]:
    """
    Get paths to API key files (AI Studio).

    Returns:
        Dictionary with 'studio' key pointing to API key file path.
    """
    gemini_dir = Path.home() / ".gemini"
    return {
        "studio": gemini_dir / "api-key-studio"
        if (gemini_dir / "api-key-studio").exists()
        else None,
    }


def load_api_key(mode: str = "studio") -> Optional[str]:
    """
    Load API key from file for the specified mode.

    Args:
        mode: Authentication mode ('studio' for AI Studio)

    Returns:
        API key if found, None otherwise.
    """
    paths = get_api_key_paths()
    key_path = paths.get(mode)

    if key_path and key_path.exists():
        try:
            return key_path.read_text().strip()
        except Exception:
            return None
    return None


def setup_vertex_env(
    project: Optional[str] = None, location: Optional[str] = None
) -> Dict[str, str]:
    """
    Setup environment variables for Vertex AI.

    If project/location are not provided, attempts to get them from gcloud config.

    Args:
        project: GCP Project ID (optional, auto-detected if None)
        location: GCP location (optional, auto-detected if None)

    Returns:
        Dictionary of environment variables that were set.
    """
    env_vars = {}

    # Get or detect project
    if project:
        env_vars["GOOGLE_CLOUD_PROJECT"] = project
    else:
        detected_project = get_gcloud_project()
        if detected_project:
            env_vars["GOOGLE_CLOUD_PROJECT"] = detected_project

    # Get or detect location
    if location:
        env_vars["GOOGLE_CLOUD_LOCATION"] = location
    else:
        # For Gemini 3, 'global' is the required endpoint.
        # We default to it even if gcloud has a different compute/region.
        env_vars["GOOGLE_CLOUD_LOCATION"] = "global"

    # SDK-specific flag for Vertex AI redirection
    env_vars["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

    # Actually set the env vars
    for key, value in env_vars.items():
        os.environ[key] = value

    # Persist to session env file
    update_session_env(env_vars)

    return env_vars


def get_mode_preference() -> Optional[str]:
    """
    Get the user's preferred authentication mode from config file.

    Returns:
        'vertex' or 'studio' if set, None if no preference.
    """
    if not KANOA_CONFIG_FILE.exists():
        return None

    try:
        config = json.loads(KANOA_CONFIG_FILE.read_text())
        return cast("Optional[str]", config.get("mode"))
    except Exception:
        return None


def set_mode_preference(mode: str) -> None:
    """
    Set the user's preferred authentication mode.

    Args:
        mode: 'vertex' or 'studio'
    """
    KANOA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config: Dict[str, Any] = {}
    with suppress(Exception):
        if KANOA_CONFIG_FILE.exists():
            config = json.loads(KANOA_CONFIG_FILE.read_text())

    config["mode"] = mode
    KANOA_CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_auth_status() -> Dict[str, Any]:
    """
    Get comprehensive authentication status.

    Returns:
        Dictionary with authentication status information:
        - mode: 'vertex' if ADC configured, 'studio' if API key found, None otherwise
        - mode_preference: User's preferred mode from config (if set)
        - project: GCP project ID (if Vertex)
        - location: GCP location (if Vertex)
        - adc_configured: bool
        - api_key_available: bool
    """
    adc_configured = check_adc_status()
    api_key_available = load_api_key("studio") is not None
    project = get_gcloud_project()
    location = get_gcloud_location()
    mode_preference = get_mode_preference()

    # Determine active mode based on preference if set, otherwise auto-detect
    mode = None
    if mode_preference == "vertex" and adc_configured and project:
        mode = "vertex"
    elif mode_preference == "studio" and api_key_available:
        mode = "studio"
    elif not mode_preference:
        # Auto-detect: prefer Vertex if available
        if adc_configured and project:
            mode = "vertex"
        elif api_key_available:
            mode = "studio"

    return {
        "mode": mode,
        "mode_preference": mode_preference,
        "project": project,
        "location": location or "us-central1",
        "adc_configured": adc_configured,
        "api_key_available": api_key_available,
    }


def print_auth_status():
    """Print authentication status in a user-friendly format."""
    status = get_auth_status()

    print("🔐 kanoa Authentication Status")
    print("=" * 50)

    if status["mode"] == "vertex":
        print("✅ Mode: Vertex AI (Application Default Credentials)")
        print(f"  Project: {status['project']}")
        print(f"  Location: {status['location']}")
    elif status["mode"] == "studio":
        print("✅ Mode: AI Studio (API Key)")
        print("  API key found in ~/.gemini/api-key-studio")
    else:
        print("❌ No authentication configured")
        print("\nSetup options:")
        print("  Vertex AI: gcloud auth application-default login")
        print("  AI Studio: Save API key to ~/.gemini/api-key-studio")

    if status["mode_preference"]:
        print(
            f"\n💡 Mode preference: {status['mode_preference']} (set via 'kanoa gemini mode')"
        )

    print("\nDetails:")
    print(f"  ADC configured: {'✅' if status['adc_configured'] else '❌'}")
    print(f"  API key available: {'✅' if status['api_key_available'] else '❌'}")
