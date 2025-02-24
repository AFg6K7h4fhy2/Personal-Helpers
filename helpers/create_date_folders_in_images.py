import argparse
import glob
import os
import re


def create_image_directories(target_dir):
    # ensure the target directory exists
    if not os.path.isdir(target_dir):
        raise NotADirectoryError(f"{target_dir} is not a valid directory.")

    # create the images folder inside the target
    # directory if it doesn't exist
    images_dir = os.path.join(target_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # glob all files (non-recursive) in the target directory
    pattern = os.path.join(target_dir, "*")
    files = glob.glob(pattern)

    # regex pattern to find dates in the format YYYY-MM-DD
    date_regex = re.compile(r"\d{4}-\d{2}-\d{2}")

    for filepath in files:
        # only process files (skip directories)
        if os.path.isfile(filepath):
            filename = os.path.basename(filepath)
            # check if filename contains a date in the format YYYY-MM-DD
            if date_regex.search(filename):
                # remove the file extension to use as directory name
                dir_name, _ = os.path.splitext(filename)
                # create the new directory inside images folder
                new_dir = os.path.join(images_dir, dir_name)
                os.makedirs(new_dir, exist_ok=True)
                print(f"Created directory: {new_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Create image directories for files with dates in their filenames."
        )
    )
    parser.add_argument("target_dir", help="Path to the target directory")

    args = parser.parse_args()

    try:
        create_image_directories(args.target_dir)
    except Exception as e:
        print(f"Error: {e}")
