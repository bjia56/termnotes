#!/usr/bin/env python3
"""
Usage:
    python add_dir_into_zip.py /path/to/source_dir /path/to/archive.zip target/sub/path/inside/zip [--dry-run]

This appends the contents of source_dir into the ZIP under the given target prefix.
"""
import os
import sys
import zipfile

def add_dir_to_zip(source_dir, zip_path, target_prefix, dry_run=False):
    source_dir = os.path.abspath(source_dir)
    # normalize target prefix (no leading slash, end with slash if not empty)
    target_prefix = target_prefix.strip("/\\")
    if target_prefix:
        target_prefix = target_prefix.rstrip("/") + "/"
    else:
        target_prefix = ""

    if dry_run:
        print(f"[DRY RUN] Would add contents of {source_dir} to {zip_path} under prefix '{target_prefix}'")
        for root, dirs, files in os.walk(source_dir):
            rel_root = os.path.relpath(root, source_dir)
            if rel_root == ".":
                rel_root = ""
            else:
                rel_root = rel_root.replace(os.path.sep, "/") + "/"

            if not files and not dirs:
                arcname = target_prefix + rel_root
                print(f"[DRY RUN]   Would add empty directory: {arcname}")

            for f in files:
                full = os.path.join(root, f)
                arcname = target_prefix + rel_root + f
                arcname = arcname.replace(os.path.sep, "/")
                print(f"[DRY RUN]   Would add: {arcname}")
    else:
        with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                rel_root = os.path.relpath(root, source_dir)
                if rel_root == ".":
                    rel_root = ""
                else:
                    rel_root = rel_root.replace(os.path.sep, "/") + "/"

                # Ensure empty directories are represented
                if not files and not dirs:
                    zf.writestr(target_prefix + rel_root, "")

                for f in files:
                    full = os.path.join(root, f)
                    arcname = target_prefix + rel_root + f
                    arcname = arcname.replace(os.path.sep, "/")
                    zf.write(full, arcname)

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--dry-run"]

    if len(args) != 3:
        print("Usage: python add_dir_into_zip.py SOURCE_DIR ARCHIVE_ZIP TARGET/PREFIX/IN/ZIP [--dry-run]")
        sys.exit(2)

    src, archive, prefix = args[0], args[1], args[2]
    add_dir_to_zip(src, archive, prefix, dry_run)

    if not dry_run:
        print(f"Added {src} -> {archive} under prefix '{prefix}'")