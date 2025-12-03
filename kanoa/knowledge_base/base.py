import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from ..config import options
from ..utils.logging import log_error, log_info, log_warning


class BaseKnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""

    def __init__(self, kb_path: Optional[Union[str, Path]] = None):
        self.kb_path = Path(kb_path) if kb_path else None

    def add_resource(self, uri: str, filename: Optional[str] = None) -> Path:
        """
        Add a resource (file) to the knowledge base from a URI.
        Supports http://, https://, gs://, and local paths.

        Args:
            uri: Source URI.
            filename: Optional destination filename. If None, inferred from URI.

        Returns:
            Path to the added file.
        """
        # Lazily create a directory if no path exists
        if not self.kb_path:
            # Use configured default home or fallback to temp
            if options.kb_home:
                self.kb_path = options.kb_home
                log_info(
                    f"Using default knowledge base path: {self.kb_path}",
                    source="kanoa.knowledge_base",
                )
            else:
                self.kb_path = Path(tempfile.mkdtemp(prefix="kanoa_kb_"))
                log_warning(
                    f"No kb_path set. Using temporary directory: {self.kb_path}",
                    source="kanoa.knowledge_base",
                )

        # Ensure directory exists
        self.kb_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if not filename:
            filename = Path(uri).name
            # Remove query parameters if present in URL
            if "?" in filename:
                filename = filename.split("?")[0]

        dest_path = self.kb_path / filename

        # Handle different protocols
        if uri.startswith(("http://", "https://")):
            # Auto-encode URL to handle spaces, parentheses, etc.
            # We preserve :/?=& to keep the URL structure intact
            uri = urllib.parse.quote(uri, safe=":/?=&")

            log_info(
                f"Downloading {uri} to {dest_path}...",
                source="kanoa.knowledge_base",
            )
            try:
                # Use a custom user agent to avoid 403s from some sites
                req = urllib.request.Request(uri, headers={"User-Agent": "kanoa/0.1.0"})
                with (
                    urllib.request.urlopen(req) as response,
                    open(dest_path, "wb") as out_file,
                ):
                    shutil.copyfileobj(response, out_file)
            except Exception as e:
                log_error(
                    f"Error downloading {uri}: {e}",
                    source="kanoa.knowledge_base",
                    context={"uri": uri, "error": str(e)},
                )
                raise e

        elif uri.startswith("gs://"):
            log_info(
                f"Downloading {uri} to {dest_path}...",
                source="kanoa.knowledge_base",
            )
            # Try using google-cloud-storage if available
            try:
                from google.cloud import (
                    storage,  # type: ignore[import-untyped, unused-ignore]
                )

                # Parse bucket and blob name
                # gs://bucket-name/path/to/blob
                parts = uri[5:].split("/", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid GCS URI: {uri}")
                bucket_name, blob_name = parts

                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename(str(dest_path))
                return dest_path

            except ImportError:
                # Fallback to CLI tools if library not installed
                pass
            except Exception as e:
                # If library installed but fails (e.g. auth), try CLI
                log_warning(
                    f"Google Cloud Storage API failed: {e}. "
                    f"Falling back to CLI tools...",
                    source="kanoa.knowledge_base",
                    context={"error": str(e)},
                )

            try:
                # Try gcloud storage cp first (faster, modern)
                subprocess.run(
                    ["gcloud", "storage", "cp", uri, str(dest_path)],
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Fallback to gsutil
                    subprocess.run(
                        ["gsutil", "cp", uri, str(dest_path)],
                        check=True,
                        capture_output=True,
                    )
                except Exception as e:
                    log_error(
                        f"Error downloading {uri}: {e}. "
                        "Ensure 'gcloud' or 'gsutil' is installed and authenticated. "
                        "Or install the Python client: pip install 'kanoa[gcloud]'",
                        source="kanoa.knowledge_base",
                        context={"uri": uri, "error": str(e)},
                    )
                    raise e

        else:
            # Assume local path
            src_path = Path(uri)
            if src_path.exists():
                if src_path.resolve() != dest_path.resolve():
                    shutil.copy2(src_path, dest_path)
            else:
                raise FileNotFoundError(f"Local file not found: {uri}")

        return dest_path

    @abstractmethod
    def get_context(self) -> str:
        """Get knowledge base context as string."""

    @abstractmethod
    def reload(self) -> None:
        """Reload knowledge base content."""
