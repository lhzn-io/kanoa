import sys
import urllib.request
from pathlib import Path


def ensure_demo_asset(
    filename: str,
    url: str,
    dir_name: str = "knowledge_base_demo",
    verbose: bool = True,
) -> Path:
    """
    Ensure a demo asset exists, downloading it if necessary.

    Args:
        filename: Name of the file to save.
        url: URL to download from.
        dir_name: Directory to save the file in (relative to CWD or script location).
        verbose: Whether to print status messages.

    Returns:
        Path to the downloaded file.
    """
    # Determine base directory
    # If running as a script, use script's directory
    # If running in notebook/interactive, use CWD
    base_dir = Path.cwd()

    # Try to detect if we are in a script file to be relative to it
    # This is a heuristic
    main_module = sys.modules.get("__main__")
    main_file = getattr(main_module, "__file__", None)
    if main_file:
        base_dir = Path(main_file).parent

    target_dir = base_dir / dir_name
    target_path = target_dir / filename

    # Ensure directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Download if not exists
    if not target_path.exists():
        if verbose:
            print(f"Downloading demo asset from {url}...")
        try:
            urllib.request.urlretrieve(url, target_path)
            if verbose:
                print("Download complete.")
        except Exception as e:
            if verbose:
                print(f"❌ Error downloading file: {e}")
            raise e

    if verbose:
        print(f"Asset ready: {target_path}")
        if target_path.exists():
            file_size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")

    return target_path
