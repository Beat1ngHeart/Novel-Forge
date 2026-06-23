"""File service — handles file storage, hashing, MIME detection, and security."""

from __future__ import annotations

import hashlib
import mimetypes
import re
import unicodedata
from pathlib import Path

from app.core.config import settings

ALLOWED_EXTENSIONS = {ext.strip() for ext in settings.UPLOAD_ALLOWED_EXTENSIONS.split(",")}
MAX_SIZE_BYTES = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024

# Dangerous extensions that must never be accepted
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".msi",
    ".scr",
    ".pif",
    ".sh",
    ".bash",
    ".zsh",
    ".csh",
    ".py",
    ".rb",
    ".pl",
    ".php",
    ".js",
    ".vbs",
    ".ps1",
    ".dll",
    ".so",
    ".dylib",
    ".app",
    ".dmg",
    ".jar",
    ".war",
    ".ear",
    ".cgi",
    ".asp",
    ".aspx",
    ".jsp",
}

# MIME types allowed for text content
ALLOWED_MIME_PREFIXES = ("text/",)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters.

    - Normalize unicode
    - Remove path separators and null bytes
    - Remove control characters
    - Collapse whitespace
    - Limit length
    """
    # Normalize unicode (NFC form)
    name = unicodedata.normalize("NFC", filename)

    # Extract just the basename (no directory components)
    name = Path(name).name

    # Remove null bytes
    name = name.replace("\x00", "")

    # Remove path separators (defense in depth)
    name = name.replace("/", "_").replace("\\", "_")

    # Remove control characters
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)

    # Collapse multiple spaces/dots
    name = re.sub(r"\s+", " ", name).strip()

    # If empty after sanitization, use a default
    if not name:
        name = "unnamed_file"

    # Limit length (keep extension)
    if len(name) > 200:
        ext = Path(name).suffix
        name = name[: 200 - len(ext)] + ext

    return name


def validate_extension(filename: str) -> str:
    """Validate file extension. Returns error message or empty string."""
    ext = Path(filename).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return f"不允许上传可执行文件: {ext}"
    if ext not in ALLOWED_EXTENSIONS:
        return f"不支持的文件类型: {ext}，允许: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    return ""


def validate_file(filename: str, file_size: int) -> str:
    """Validate file type and size. Returns error message or empty string."""
    error = validate_extension(filename)
    if error:
        return error
    if file_size > MAX_SIZE_BYTES:
        return f"文件过大: {file_size / 1024 / 1024:.1f}MB，最大 {settings.UPLOAD_MAX_SIZE_MB}MB"
    if file_size == 0:
        return "文件为空"
    return ""


def detect_mime_type(filename: str, data: bytes) -> str:
    """Detect MIME type from filename and content."""
    # Try Python's mimetypes first
    mime, _ = mimetypes.guess_type(filename)
    if mime:
        return mime

    # Check if content is valid UTF-8 text
    try:
        data.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        pass

    # Check for common text encodings
    for enc in ("gbk", "gb2312", "big5", "shift_jis"):
        try:
            data.decode(enc)
            return "text/plain"
        except (UnicodeDecodeError, LookupError):
            continue

    return "application/octet-stream"


def validate_mime(mime_type: str) -> str:
    """Validate that MIME type is allowed. Returns error message or empty string."""
    if not any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        return f"不允许的文件类型: {mime_type}，只接受文本文件"
    return ""


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_encoding(raw: bytes) -> str:
    """Try common encodings."""
    for enc in ("utf-8", "gbk", "gb2312", "big5", "shift_jis"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def generate_stored_filename(original_filename: str, sha256: str) -> str:
    """Generate a safe stored filename using SHA-256 prefix."""
    safe_name = sanitize_filename(original_filename)
    ext = Path(safe_name).suffix.lower()
    return f"{sha256[:16]}{ext}"


def save_file(project_id: str, filename: str, data: bytes) -> Path:
    """Save file to disk under uploads/{project_id}/{safe_name}.

    Returns the stored path. The path is always within the upload directory.
    """
    upload_dir = Path(settings.UPLOAD_DIR) / sanitize_filename(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_name = generate_stored_filename(filename, compute_sha256(data))
    file_path = upload_dir / stored_name

    # Verify the resolved path is within upload directory (defense against path traversal)
    try:
        file_path.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
    except ValueError:
        raise ValueError("Invalid file path")

    file_path.write_bytes(data)
    return file_path


def cleanup_file(file_path: str) -> None:
    """Delete a file from disk if it exists. Safe against path traversal."""
    p = Path(file_path)
    if p.exists():
        try:
            p.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
            p.unlink()
        except (ValueError, OSError):
            pass  # Don't delete files outside upload dir


def read_file_text(file_path: str) -> str:
    """Read a stored file and return its text content."""
    raw = Path(file_path).read_bytes()
    encoding = detect_encoding(raw)
    return raw.decode(encoding)


def file_rights_defaults(rights_status: str) -> dict:
    """Return default analysis_allowed and generation_reference_allowed based on rights status."""
    if rights_status == "prohibited":
        return {"analysis_allowed": False, "generation_reference_allowed": False}
    if rights_status in ("unknown",):
        return {"analysis_allowed": True, "generation_reference_allowed": False}
    if rights_status == "analysis_only":
        return {"analysis_allowed": True, "generation_reference_allowed": False}
    # owned, authorized, public_domain
    return {"analysis_allowed": True, "generation_reference_allowed": True}
