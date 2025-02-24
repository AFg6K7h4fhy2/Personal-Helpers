import argparse
import glob
import json
import os
import re
import subprocess


def parse_identify_output(text: str) -> dict:
    """
    Parse the verbose output from 'magick identify -verbose' into a
    nested dictionary. This simple parser uses indentation to infer nesting.
    """
    result = {}
    stack = [(0, result)]

    for line in text.splitlines():
        if not line.strip():
            continue

        # determine indentation (number of leading spaces)
        indent = len(line) - len(line.lstrip())

        # match lines of the form "Key: value"
        m = re.match(r"^\s*(.+?):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()

        # pop stack until we find the correct parent level
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else result

        # if the value is empty, create a new nested dictionary.
        if value == "":
            new_dict = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))
        else:
            # if the key already exists, convert it to a list of values.
            if key in parent:
                if not isinstance(parent[key], list):
                    parent[key] = [parent[key]]
                parent[key].append(value)
            else:
                parent[key] = value
    return result


def process_heic_images(target_path: str):
    # verify that the target_path is a directory
    if not os.path.isdir(target_path):
        print(f"Error: {target_path} is not a valid directory.")
        return

    # use glob to get all HEIC files (case-insensitive)
    heic_paths = glob.glob(os.path.join(target_path, "*.HEIC"))
    heic_paths += glob.glob(os.path.join(target_path, "*.heic"))

    if not heic_paths:
        print("No HEIC files found in the specified directory.")
    else:
        # process each HEIC file for metadata extraction
        for file_path in heic_paths:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            metadata_file = os.path.join(
                target_path, f"{base_name}_metadata.json"
            )
            print(f"Collecting metadata from {file_path}...")
            try:
                result = subprocess.run(
                    ["magick", "identify", "-verbose", file_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # parse the verbose output into a dictionary
                metadata_dict = parse_identify_output(result.stdout)
                # write the metadata dictionary as JSON
                with open(metadata_file, "w") as mf:
                    json.dump(metadata_dict, mf, indent=2)
                print(f"Metadata written to {metadata_file}.")
            except subprocess.CalledProcessError as e:
                print(f"Error collecting metadata from {file_path}: {e}.")

    # convert HEIC images to JPG at 80% quality
    if heic_paths:
        print("Converting HEIC images to JPG with 80% quality...")
        convert_command = [
            "magick",
            "mogrify",
            "-format",
            "jpg",
            "-quality",
            "80%",
        ] + heic_paths
        try:
            subprocess.run(convert_command, check=True)
            print("Conversion complete.")
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")

    # strip metadata from the newly created JPG files
    jpg_paths = glob.glob(os.path.join(target_path, "*.jpg"))
    if jpg_paths:
        print("Stripping metadata from JPG files...")
        strip_command = ["magick", "mogrify", "-strip"] + jpg_paths
        try:
            subprocess.run(strip_command, check=True)
            print("Metadata stripped from JPG files.")
        except subprocess.CalledProcessError as e:
            print(f"Error stripping metadata: {e}")

    # delete the original HEIC files
    if heic_paths:
        print("Deleting original HEIC files...")
        delete_command = ["rm", "-f"] + heic_paths
        try:
            subprocess.run(delete_command, check=True)
            print("Original HEIC files deleted.")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting HEIC files: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Process HEIC images: extract metadata (as JSON), convert to JPG, "
            "strip metadata from the JPEGs, and delete the originals."
        )
    )
    parser.add_argument(
        "target_directory",
        help="Path to the directory containing HEIC images.",
    )
    args = parser.parse_args()
    process_heic_images(args.target_directory)
