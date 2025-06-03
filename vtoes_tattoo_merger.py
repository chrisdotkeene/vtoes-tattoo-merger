import os
import subprocess
import sys
import shutil

try:
    from PIL import Image
except ImportError:
    print("📦 'Pillow' not found. Attempting to install from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip3", "install", "-r", "requirements.txt"])
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run:")
            print("   pip install -r requirements.txt")
            input("\nPress Enter to exit...")
            sys.exit(1)
    from PIL import Image

SCRIPT_DIR = os.getcwd()
GAMEPATH = "C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077"
TARGET_XBM_PATH = os.path.normpath("base/4k/common/overlays/fullbody_overlay_d01.xbm")
EXTRACTION_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "extracted")
IMPORT_DIR = os.path.join(SCRIPT_DIR, "import")

archives = [
    f for f in os.listdir(SCRIPT_DIR)
    if f.endswith(".archive") and not f.startswith("patched_")
]
if not archives:
    print("❌ No .archive files found.")
    input("Press Enter to exit...")
    sys.exit(1)

print("Available archives:")
for i, name in enumerate(archives):
    print(f"{i+1}: {name}")
try:
    ARCHIVE_NAME = archives[int(input("Select archive by number: ")) - 1]
except Exception as e:
    print(f"\n❌ Failed to select archive: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

def run_cmd(cmd, description, fail=True):
    print(f"\n>>> {description}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    def clean(output):
        return "\n".join(
            [line for line in output.splitlines() if "Unknown file extension" not in line]
        )
    if result.stdout.strip():
        print("--- STDOUT ---")
        print(clean(result.stdout))
    if result.stderr.strip():
        print("--- STDERR ---")
        print(clean(result.stderr))
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        if fail:
            sys.exit(result.returncode)
    return result

def extract_archive():
    print("\n[Step 1] Extracting XBM")
    if os.path.exists(EXTRACTION_OUTPUT_DIR):
        print(f"Removing existing directory: {EXTRACTION_OUTPUT_DIR}")
        shutil.rmtree(EXTRACTION_OUTPUT_DIR)
    os.makedirs(EXTRACTION_OUTPUT_DIR)
    print(f"Created directory: {EXTRACTION_OUTPUT_DIR}")

    archive_path = os.path.join(SCRIPT_DIR, ARCHIVE_NAME)
    uncook_cmd = [
        "cp77tools", "uncook",
        "-p", archive_path,
        "-o", EXTRACTION_OUTPUT_DIR,
        "--uext", "png"
    ]
    run_cmd(uncook_cmd, "Uncooking archive to extract XBM and PNG", fail=False)

    xbm_file = os.path.join(EXTRACTION_OUTPUT_DIR, TARGET_XBM_PATH)
    png_file = os.path.splitext(xbm_file)[0] + ".png"
    if not os.path.isfile(png_file):
        print(f"❌ PNG not found: {png_file}")
        input("Press Enter to exit...")
        sys.exit(1)

    return png_file, xbm_file

def copy_preserving_structure(src_root, dst_root, keep_exts=None, skip_exts=None):
    for root, _, files in os.walk(src_root):
        rel_path = os.path.relpath(root, src_root)
        dst_path = os.path.join(dst_root, rel_path)
        os.makedirs(dst_path, exist_ok=True)
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if skip_exts and ext in skip_exts:
                continue
            if keep_exts and ext not in keep_exts:
                continue
            shutil.copy2(os.path.join(root, file), os.path.join(dst_path, file))

def merge_overlay(base_png_path):
    print("\n[Step 2] Merging overlay")
    base_img = Image.open(base_png_path).convert("RGBA")
    overlay_img = Image.open(TOENAIL_PATH).convert("RGBA")
    r, g, b, a = overlay_img.split()
    safe_alpha = a.point(lambda p: max(p, 1))
    overlay_img = Image.merge("RGBA", (r, g, b, safe_alpha))

    merged = base_img.copy()
    merged.paste(overlay_img, (0, 0), overlay_img)

    import_png_path = os.path.join(
        IMPORT_DIR, os.path.splitext(TARGET_XBM_PATH)[0] + ".png"
    )
    os.makedirs(os.path.dirname(import_png_path), exist_ok=True)
    merged.save(import_png_path)
    print(f"Saved merged image to: {import_png_path}")

    return import_png_path

def import_merged_png(final_png_path, xbm_source_path):
    print("\n[Step 3] Importing PNG as XBM")
    xbm_target_path = os.path.join(IMPORT_DIR, TARGET_XBM_PATH)
    os.makedirs(os.path.dirname(xbm_target_path), exist_ok=True)

    if not os.path.exists(xbm_target_path) and os.path.exists(xbm_source_path):
        shutil.copy2(xbm_source_path, xbm_target_path)
        print(f"Copied original XBM to: {xbm_target_path}")

    import_cmd = [
        "cp77tools", "import",
        "-p", final_png_path,
        "-o", os.path.dirname(xbm_target_path)
    ]
    run_cmd(import_cmd, "Importing PNG into XBM")

def pack_archive():
    print("\n[Step 4] Packing archive")
    archive_base = os.path.splitext(ARCHIVE_NAME)[0]
    out_path = os.path.join(SCRIPT_DIR, f"{archive_base}_V-Toes_{TOENAIL_COLOR}")
    pack_cmd = [
        "cp77tools", "pack",
        "-i", IMPORT_DIR,
        "-o", out_path,
        "--gamepath", GAMEPATH
    ]
    run_cmd(pack_cmd, f"Packing to {out_path}")
    print(f"✅ Final archive created: {out_path}")

    cyberjunk = os.path.join(out_path, "Cyberpunk 2077.archive")
    if os.path.exists(cyberjunk):
        os.remove(cyberjunk)
        print(f"🗑️ Deleted: {cyberjunk}")

    source_archive = os.path.join(out_path, "import.archive")
    target_archive = os.path.join(
        out_path, f"{archive_base}_V-Toes_{TOENAIL_COLOR}.archive"
    )
    if os.path.exists(source_archive):
        os.rename(source_archive, target_archive)
        print(f"🔁 Renamed import.archive → {os.path.basename(target_archive)}")
    else:
        print("❌ import.archive not found.")

if __name__ == "__main__":
    shutil.rmtree(EXTRACTION_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(IMPORT_DIR, ignore_errors=True)

    try:
        extracted_png, xbm_path = extract_archive()

        EXTRACTED_BASE = os.path.join(EXTRACTION_OUTPUT_DIR, "base")
        IMPORT_BASE = os.path.join(IMPORT_DIR, "base")
        copy_preserving_structure(EXTRACTED_BASE, IMPORT_BASE, skip_exts={".png"})

        base_img = Image.open(extracted_png)
        width, height = base_img.size
        if width == 4096 and height == 4096:
            color_size_folder = "4k"
        elif width == 8192 and height == 8192:
            color_size_folder = "8k"
        else:
            print(f"❌ Unsupported resolution: {width}x{height}")
            input("Press Enter to exit...")
            sys.exit(1)

        colors_path = os.path.join(SCRIPT_DIR, "colors", color_size_folder)
        colors = [f for f in os.listdir(colors_path) if f.endswith(".png")]
        if not colors:
            print(f"❌ No PNG colors found in 'colors/{color_size_folder}/' directory.")
            input("Press Enter to exit...")
            sys.exit(1)

        print(f"\nAvailable {color_size_folder} overlay colors:")
        for i, name in enumerate(colors):
            print(f"{i+1}: {name}")
        try:
            selected_color = colors[int(input("Select color by number: ")) - 1]
        except Exception as e:
            print(f"\n❌ Failed to select color: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

        TOENAIL_COLOR = os.path.splitext(selected_color)[0]
        TOENAIL_PATH = os.path.join(colors_path, selected_color)

        merged_png = merge_overlay(extracted_png)
        import_merged_png(merged_png, xbm_path)

        if TOENAIL_COLOR.startswith("metallic_") or TOENAIL_COLOR in ("chrome", "gold"):
            extra_xbm_src = os.path.join(SCRIPT_DIR, "wa_base_rm02.xbm")
            if os.path.exists(extra_xbm_src):
                extra_target_dir = os.path.join(
                    IMPORT_DIR, "base", "4k", "common", "body", "wa", "textures"
                )
                os.makedirs(extra_target_dir, exist_ok=True)
                extra_target_path = os.path.join(extra_target_dir, os.path.basename(extra_xbm_src))
                shutil.copy2(extra_xbm_src, extra_target_path)
                print(f"📦 Included metallic XBM: {extra_target_path}")
            else:
                print("❌ wa_base_rm02.xbm not found in script folder!")

        pack_archive()

        shutil.rmtree(EXTRACTION_OUTPUT_DIR, ignore_errors=True)
        shutil.rmtree(IMPORT_DIR, ignore_errors=True)
        print("🧹 Cleaned up temporary folders.")

    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        print("⚠️ Temporary folders were not deleted to help with debugging.")
        input("\nPress Enter to exit...")
        sys.exit(1)
