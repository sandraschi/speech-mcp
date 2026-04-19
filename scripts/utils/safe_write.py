import os
import shutil
import json
import logging
import argparse
import tempfile
import re
from datetime import datetime
from pathlib import Path

# Configure logging with SOTA standards
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("safe_write")

def count_structures(content: str):
    """Counts classes and functions to detect structural regression."""
    defs = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
    classes = len(re.findall(r"^\s*class\s+\w+", content, re.MULTILINE))
    return defs, classes

def safe_write(target_path: str, content: str, author: str = "Assistant", force: bool = False):
    target = Path(target_path).resolve()
    target_dir = target.parent
    filename = target.name
    new_size = len(content.encode("utf-8"))

    # 1. Dialogic Validation (Pre-flight / Basic)
    if not target_dir.exists():
        return {
            "success": False,
            "error": "DirectoryNotFound",
            "message": f"The parent directory '{target_dir}' does not exist.",
            "dialogic": {
                "suggestion": "Identify if you are creating a new project or path. If this is a test (e.g. Starfleet/Coco), acknowledge the Joke path.",
                "remediation": f"New-Item -ItemType Directory -Path '{target_dir}' -Force",
                "is_test_or_joke": "starfleet" in str(target).lower() or "coco" in str(target).lower()
            }
        }

    # 2. Ironclad Anti-Stub Protection
    if target.exists() and not force:
        existing_content = target.read_text(encoding="utf-8", errors="ignore")
        existing_size = len(existing_content.encode("utf-8"))
        
        e_defs, e_classes = count_structures(existing_content)
        n_defs, n_classes = count_structures(content)
        
        # Heuristic A: Significant Size Regression
        if existing_size > 500 and new_size < (existing_size * 0.25):
            return {
                "success": False,
                "error": "SizeRegressionAlert",
                "message": f"Stub detected! Existing file is {existing_size} bytes; new content is only {new_size} bytes.",
                "dialogic": {
                    "suggestion": "You are attempting to replace a functional file with a trivial stub. This is a high-risk operation.",
                    "remediation": "read_file(target)",
                    "action_required": "USE --force TO OVERWRITE"
                }
            }

        # Heuristic B: Structural Regression
        if (e_defs + e_classes) > 2 and (n_defs + n_classes) <= ((e_defs + e_classes) // 2):
            return {
                "success": False,
                "error": "StructuralRegressionAlert",
                "message": f"Stub detected! Existing file has {e_defs} defs/ {e_classes} classes; new content has only {n_defs}/{n_classes}.",
                "dialogic": {
                    "suggestion": "The new content is missing the majority of the existing code's logic/structure.",
                    "remediation": "Check your context. Did you actually find the file content or are you hallucinating a replacement?",
                    "action_required": "USE --force TO OVERWRITE"
                }
            }

    # 3. Local Backup (Side-car)
    backup_dir = target_dir / ".backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_bak = backup_dir / f"{timestamp}_{filename}.bak"
    
    if target.exists():
        shutil.copy2(target, local_bak)
        logger.info(f"Local backup created: {local_bak}")

    # 4. Global Fleet Archive
    archive_log = Path("D:/Dev/fleet_archive/global_history.jsonl")
    try:
        with open(archive_log, "a", encoding="utf-8") as f:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "file": str(target),
                "author": author,
                "existing_size": os.path.getsize(target) if target.exists() else 0,
                "new_size": new_size,
                "backup_path": str(local_bak) if target.exists() else None,
                "force_used": force
            }
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write to central fleet archive: {e}")

    # 5. Atomic Write Procedure
    try:
        with tempfile.NamedTemporaryFile("w+", dir=target_dir, delete=False, encoding="utf-8", suffix=".tmp") as tmp:
            tmp.write(content)
            tmp_name = tmp.name

        if len(content) > 0 and os.path.getsize(tmp_name) == 0:
            raise IOError("Temp file verification failed: File is 0 bytes.")

        os.replace(tmp_name, target)
        logger.info(f"Atomic write successful: {target}")

        return {
            "success": True,
            "file": str(target),
            "size": new_size,
            "backup": str(local_bak) if local_bak.exists() else None
        }

    except Exception as e:
        if 'tmp_name' in locals() and os.path.exists(tmp_name):
            os.remove(tmp_name)
            
        return {
            "success": False,
            "error": "WriteFailure",
            "message": str(e),
            "dialogic": {
                "suggestion": "Disk may be full or permissions denied.",
                "remediation": "Verify disk space and file locks."
            }
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOTA Ironclad Safe-Write Utility")
    parser.add_argument("file", help="Target file path")
    parser.add_argument("--content", required=True, help="New file content")
    parser.add_argument("--author", default="Assistant", help="Change author")
    parser.add_argument("--force", action="store_true", help="Force overwrite despite regression alerts")
    
    args = parser.parse_args()
    
    result = safe_write(args.file, args.content, args.author, args.force)
    print(json.dumps(result, indent=2))
