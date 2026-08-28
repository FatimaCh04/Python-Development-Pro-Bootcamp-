import os
import shutil
from pathlib import Path
from datetime import datetime


# ============================================================
# FILE ORGANIZER
# Day 86 — 100 Days of Python
# ============================================================


# File categories and their extensions
FILE_CATEGORIES = {
    "Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        ".ico"
    ],

    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt"
    ],

    "Spreadsheets": [
        ".xls",
        ".xlsx",
        ".csv",
        ".ods"
    ],

    "Presentations": [
        ".ppt",
        ".pptx",
        ".odp"
    ],

    "Videos": [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm"
    ],

    "Audio": [
        ".mp3",
        ".wav",
        ".aac",
        ".flac",
        ".ogg",
        ".m4a"
    ],

    "Archives": [
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz"
    ],

    "Programs": [
        ".exe",
        ".msi",
        ".apk",
        ".bat",
        ".sh"
    ],

    "Code": [
        ".py",
        ".js",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".php",
        ".sql",
        ".json",
        ".xml"
    ]
}


# ============================================================
# Get Category
# ============================================================

def get_category(extension):

    extension = extension.lower()

    for category, extensions in FILE_CATEGORIES.items():

        if extension in extensions:
            return category

    return "Others"


# ============================================================
# Create Folder
# ============================================================

def create_folder(folder_path):

    folder_path.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# Generate Unique File Name
# ============================================================

def get_unique_path(destination):

    if not destination.exists():
        return destination

    counter = 1

    while True:

        new_name = (
            f"{destination.stem}_{counter}"
            f"{destination.suffix}"
        )

        new_path = destination.parent / new_name

        if not new_path.exists():
            return new_path

        counter += 1


# ============================================================
# Organize Files
# ============================================================

def organize_files(folder):

    folder = Path(folder)

    if not folder.exists():

        print("\n❌ Folder does not exist.")
        return

    if not folder.is_dir():

        print("\n❌ The selected path is not a folder.")
        return


    moved_files = 0
    skipped_files = 0


    print("\n" + "=" * 55)
    print("           FILE ORGANIZATION STARTED")
    print("=" * 55)


    for item in folder.iterdir():

        # Ignore folders
        if item.is_dir():
            continue

        # Ignore this Python script
        if item.name == Path(__file__).name:
            continue


        extension = item.suffix

        category = get_category(extension)


        # Create category folder
        category_folder = folder / category

        create_folder(category_folder)


        # Create destination path
        destination = category_folder / item.name

        # Prevent overwriting
        destination = get_unique_path(destination)


        try:

            shutil.move(
                str(item),
                str(destination)
            )

            print(
                f"✓ {item.name}  →  {category}/"
            )

            moved_files += 1

        except PermissionError:

            print(
                f"⚠ Permission denied: {item.name}"
            )

            skipped_files += 1

        except Exception as error:

            print(
                f"⚠ Could not move {item.name}: {error}"
            )

            skipped_files += 1


    print("\n" + "=" * 55)
    print("           ORGANIZATION COMPLETED")
    print("=" * 55)

    print(f"\nFiles organized : {moved_files}")
    print(f"Files skipped   : {skipped_files}")

    print("\n✓ Done!")


# ============================================================
# Preview Files
# ============================================================

def preview_files(folder):

    folder = Path(folder)

    if not folder.exists():

        print("\n❌ Folder does not exist.")
        return


    print("\n" + "=" * 55)
    print("                PREVIEW")
    print("=" * 55)


    files_found = 0


    for item in folder.iterdir():

        if item.is_file():

            if item.name == Path(__file__).name:
                continue

            category = get_category(
                item.suffix
            )

            print(
                f"{item.name:<35} → {category}"
            )

            files_found += 1


    if files_found == 0:

        print("\nNo files found.")


# ============================================================
# Show Statistics
# ============================================================

def show_statistics(folder):

    folder = Path(folder)

    statistics = {}


    for item in folder.iterdir():

        if not item.is_file():
            continue

        if item.name == Path(__file__).name:
            continue

        category = get_category(
            item.suffix
        )

        statistics[category] = (
            statistics.get(category, 0) + 1
        )


    print("\n" + "=" * 55)
    print("              FILE STATISTICS")
    print("=" * 55)


    if not statistics:

        print("\nNo files found.")
        return


    total = 0


    for category, count in sorted(
        statistics.items()
    ):

        print(
            f"{category:<20} : {count}"
        )

        total += count


    print("-" * 55)

    print(
        f"{'Total Files':<20} : {total}"
    )


# ============================================================
# Main Menu
# ============================================================

def main():

    print("\n")
    print("=" * 55)
    print("             📁 FILE ORGANIZER")
    print("=" * 55)
    print("             Day 86 — Python")
    print("=" * 55)


    folder = input(
        "\nEnter the folder path to organize:\n> "
    ).strip()


    # Remove quotes if user pasted a quoted path
    folder = folder.strip('"').strip("'")


    folder_path = Path(folder)


    if not folder_path.exists():

        print("\n❌ Folder not found.")
        return


    while True:

        print("\n")
        print("-" * 55)
        print("MENU")
        print("-" * 55)

        print("1. Preview files")
        print("2. Show statistics")
        print("3. Organize files")
        print("4. Change folder")
        print("5. Exit")


        choice = input(
            "\nChoose an option: "
        ).strip()


        if choice == "1":

            preview_files(
                folder_path
            )


        elif choice == "2":

            show_statistics(
                folder_path
            )


        elif choice == "3":

            confirmation = input(
                "\nOrganize all files? (y/n): "
            ).lower().strip()


            if confirmation == "y":

                organize_files(
                    folder_path
                )

            else:

                print(
                    "\nOperation cancelled."
                )


        elif choice == "4":

            new_folder = input(
                "\nEnter new folder path:\n> "
            ).strip()


            new_folder = (
                new_folder
                .strip('"')
                .strip("'")
            )


            new_path = Path(
                new_folder
            )


            if new_path.exists() and new_path.is_dir():

                folder_path = new_path

                print(
                    "\n✓ Folder changed successfully."
                )

            else:

                print(
                    "\n❌ Invalid folder path."
                )


        elif choice == "5":

            print(
                "\nThanks for using File Organizer! 👋"
            )

            break


        else:

            print(
                "\n❌ Invalid option. "
                "Please choose 1-5."
            )


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == "__main__":

    start_time = datetime.now()

    main()

    end_time = datetime.now()

    duration = end_time - start_time

    print(
        f"\nSession duration: {duration}"
    )