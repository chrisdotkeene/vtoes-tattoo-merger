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

script_dir = os.getcwd()
game_path = r"C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077"
# Default assumes KSUV overlay path; will be overridden if user picks VTK
target_xbm_relative = os.path.normpath("base/4k/common/overlays/fullbody_overlay_d01.xbm")

extracted_folder = os.path.join(script_dir, "extracted")
import_folder    = os.path.join(script_dir, "import")

# 1) List all .archive files in the current directory
all_archives = [
    name for name in os.listdir(script_dir)
    if name.endswith(".archive") and not name.startswith("patched_")
]
if not all_archives:
    print("❌ No .archive files found.")
    input("Press Enter to exit...")
    sys.exit(1)

print("Available archives:")
for idx, name in enumerate(all_archives, start=1):
    print(f"{idx}: {name}")
try:
    choice       = int(input("Select archive by number: ")) - 1
    archive_name = all_archives[choice]
except:
    print("\n❌ Invalid selection")
    input("Press Enter to exit...")
    sys.exit(1)

# 2) Prompt user for KSUV vs. VTK
print("\nAvailable model types:")
print("1: KSUV")
print("2: VTK")
try:
    model_choice = int(input("Select model by number: "))
except:
    print("\n❌ Invalid selection")
    input("Press Enter to exit...")
    sys.exit(1)

if model_choice == 1:
    # KSUV overlay path
    target_xbm_relative = os.path.normpath("base/4k/common/overlays/fullbody_overlay_d01.xbm")
elif model_choice == 2:
    # VTK overlay path
    target_xbm_relative = os.path.normpath("base/v_textures/body/v_overlay.xbm")
else:
    print("❌ Invalid model selection")
    input("Press Enter to exit...")
    sys.exit(1)


def run_command(cmd_list, description, abort_on_fail=True):
    """Print and run a subprocess command, then show cleaned output."""
    print(f"\n>>> {description}")
    print("Command:", " ".join(cmd_list))
    result = subprocess.run(cmd_list, capture_output=True, text=True, errors="replace")
    combined = result.stdout + result.stderr
    # Filter out “Unknown file extension” noise
    cleaned = "\n".join(line for line in combined.splitlines() if "Unknown file extension" not in line)
    if cleaned:
        print(cleaned)
    if result.returncode != 0 and abort_on_fail:
        print(f"❌ {description} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def extract_and_get_paths():
    """
    1) Delete any existing `extracted/` folder and recreate it.
    2) Run `cp77tools uncook` to extract XBM and PNG into `extracted/`.
    3) Look for the PNG that matches `target_xbm_relative`. If not found,
       fall back to checking for a top‐level PNG (e.g. `extracted/v_overlay.png`).
    Returns (png_path, xbm_path)—even if the XBM itself is missing (VTK fallback).
    """
    if os.path.exists(extracted_folder):
        shutil.rmtree(extracted_folder)
    os.makedirs(extracted_folder)

    archive_path = os.path.join(script_dir, archive_name)
    uncook = [
        "cp77tools", "uncook",
        "-p", archive_path,
        "-o", extracted_folder,
        "--uext", "png"
    ]
    run_command(uncook, "Uncooking archive to extract XBM and PNG", abort_on_fail=False)

    # 3a) Try the nested path first (e.g. extracted/base/v_textures/body/v_overlay.png)
    nested_xbm = os.path.join(extracted_folder, target_xbm_relative)
    nested_png = os.path.splitext(nested_xbm)[0] + ".png"
    if os.path.isfile(nested_png):
        return nested_png, nested_xbm

    # 3b) Fallback: search for just the filename at exrected/ root
    filename = os.path.basename(target_xbm_relative)  # e.g. "v_overlay.xbm" or "fullbody_overlay_d01.xbm"
    fallback_png = os.path.splitext(filename)[0] + ".png"  # e.g. "v_overlay.png"
    top_png = os.path.join(extracted_folder, fallback_png)
    top_xbm = os.path.join(extracted_folder, filename)

    if os.path.isfile(top_png):
        return top_png, top_xbm

    # If neither nested PNG nor top‐level PNG was found, abort
    print(f"❌ PNG not found: tried '{nested_png}' and '{top_png}'")
    input("Press Enter to exit...")
    sys.exit(1)


def copy_tree_without_png(src_root, dst_root):
    """
    Copy everything under src_root → dst_root, but skip any .png files.
    This preserves the folder structure for all other assets (XBMs, etc).
    """
    for root, _, files in os.walk(src_root):
        rel = os.path.relpath(root, src_root)
        dst = os.path.join(dst_root, rel)
        os.makedirs(dst, exist_ok=True)
        for fname in files:
            if not fname.lower().endswith(".png"):
                shutil.copy2(os.path.join(root, fname), os.path.join(dst, fname))


def merge_overlay_and_save(base_png, color_png):
    """
    Load base_png (the extracted overlay), then paste color_png on top.
    Save the result to import_folder in the same relative location as target_xbm_relative,
    but with a .png extension.
    Returns the path to that merged PNG.
    """
    base_img = Image.open(base_png).convert("RGBA")
    overlay = Image.open(color_png).convert("RGBA")
    r, g, b, a = overlay.split()
    safe_alpha = a.point(lambda p: max(p, 1))
    overlay = Image.merge("RGBA", (r, g, b, safe_alpha))

    merged = base_img.copy()
    merged.paste(overlay, (0, 0), overlay)

    save_path = os.path.join(import_folder, os.path.splitext(target_xbm_relative)[0] + ".png")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    merged.save(save_path)
    return save_path


def import_png_to_xbm(png_path, original_xbm):
    """
    If original_xbm exists, copy it into the import folder so that
    cp77tools import can use it as a template. Then run cp77tools import
    on the merged PNG to produce the final XBM in import_folder.
    """
    target_xbm = os.path.join(import_folder, target_xbm_relative)
    os.makedirs(os.path.dirname(target_xbm), exist_ok=True)

    # If the original XBM was extracted, copy it so import can preserve flags/metadata
    if os.path.exists(original_xbm) and not os.path.exists(target_xbm):
        shutil.copy2(original_xbm, target_xbm)

    cmd = ["cp77tools", "import", "-p", png_path, "-o", os.path.dirname(target_xbm)]
    run_command(cmd, "Importing PNG into XBM")


def pack_and_finalize(color_name):
    """
    Run `cp77tools pack` on import_folder to generate the new archive in out_folder.
    Then delete the auto‐generated 'Cyberpunk 2077.archive' and rename import.archive
    to <archive_base>_V-Toes_<color_name>.archive.
    """
    base_name = os.path.splitext(archive_name)[0]
    out_folder = os.path.join(script_dir, f"{base_name}_V-Toes_{color_name}")
    cmd = ["cp77tools", "pack", "-i", import_folder, "-o", out_folder, "--gamepath", game_path]
    run_command(cmd, f"Packing to {out_folder}")

    # Delete the stray “Cyberpunk 2077.archive,” if it exists
    stray = os.path.join(out_folder, "Cyberpunk 2077.archive")
    if os.path.exists(stray):
        os.remove(stray)

    # Rename import.archive → <base>_V-Toes_<color>.archive
    built = os.path.join(out_folder, "import.archive")
    final = os.path.join(out_folder, f"{base_name}_V-Toes_{color_name}.archive")
    if os.path.exists(built):
        os.rename(built, final)


if __name__ == "__main__":
    # Clean up any previous temp folders
    shutil.rmtree(extracted_folder, ignore_errors=True)
    shutil.rmtree(import_folder, ignore_errors=True)

    try:
        # 1) Extract and locate the correct overlay PNG/XBM
        extracted_png_path, original_xbm_path = extract_and_get_paths()

        # 2) Copy everything except PNGs from extracted/base → import/base
        src_base  = os.path.join(extracted_folder, "base")
        dst_base  = os.path.join(import_folder, "base")
        copy_tree_without_png(src_base, dst_base)

        # 3) Auto‐detect 4K vs 8K by opening the extracted overlay PNG
        img       = Image.open(extracted_png_path)
        w, h      = img.size
        if w == 4096 and h == 4096:
            size_folder = "4k"
        elif w == 8192 and h == 8192:
            size_folder = "8k"
        else:
            print(f"❌ Unsupported resolution: {w}x{h}")
            input("Press Enter to exit...")
            sys.exit(1)

        # 4) Determine which color folder to use
        if model_choice == 1:
            # KSUV colors live in colors/[4k or 8k]
            color_folder = os.path.join(script_dir, "colors", size_folder)
        else:
            # VTK colors live in colors/[4k or 8k]/VTK
            color_folder = os.path.join(script_dir, "colors", size_folder, "VTK")

        available_colors = [f for f in os.listdir(color_folder) if f.endswith(".png")]
        if not available_colors:
            rel = os.path.relpath(color_folder, script_dir)
            print(f"❌ No PNG colors found in '{rel}'")
            input("Press Enter to exit...")
            sys.exit(1)

        print(f"\nAvailable {size_folder} overlay colors:")
        for idx, fname in enumerate(available_colors, start=1):
            print(f"{idx}: {fname}")
        try:
            sel    = int(input("Select color by number: ")) - 1
            chosen = available_colors[sel]
        except:
            print("\n❌ Invalid selection")
            input("Press Enter to exit...")
            sys.exit(1)

        color_name = os.path.splitext(chosen)[0]
        color_path = os.path.join(color_folder, chosen)

        # 5) Merge the chosen color onto the extracted overlay PNG
        merged_png = merge_overlay_and_save(extracted_png_path, color_path)

        # 6) Import merged PNG → XBM (copy original XBM if available)
        import_png_to_xbm(merged_png, original_xbm_path)

        # 7) For KSUV, copy the metallic WA XBM if needed
        if model_choice == 1 and (color_name.startswith("metallic_") or color_name in ("chrome", "gold")):
            extra_src  = os.path.join(script_dir, "wa_base_rm02.xbm")
            if os.path.exists(extra_src):
                extra_dest = os.path.join(import_folder, "base", "4k", "common", "body", "wa", "textures")
                os.makedirs(extra_dest, exist_ok=True)
                shutil.copy2(extra_src, os.path.join(extra_dest, os.path.basename(extra_src)))

        # 8) Pack the final archive and cleanup
        pack_and_finalize(color_name)

        shutil.rmtree(extracted_folder, ignore_errors=True)
        shutil.rmtree(import_folder, ignore_errors=True)
        print("🧹 Cleaned up temporary folders.")

    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        print("⚠️ Temporary folders were not deleted to help with debugging.")
        input("Press Enter to exit...")
        sys.exit(1)
