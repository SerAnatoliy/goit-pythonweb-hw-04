import asyncio
from pathlib import Path
import logging
import argparse
import aiofiles
from colorama import Fore, Style

# Configure logging
CUSTOM_INFO = 25  # Define a custom log level
logging.addLevelName(CUSTOM_INFO, "CUSTOM_INFO")


class CustomFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        CUSTOM_INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        level_color = self.LEVEL_COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL
        levelname = f"{level_color}{record.levelname}{reset}"

        message_color = self.LEVEL_COLORS.get(record.levelno, "")
        record.msg = f"{message_color}{record.msg}{reset}"

        formatted_message = super().format(record)
        return formatted_message.replace(record.levelname, levelname)


handler = logging.StreamHandler()
formatter = CustomFormatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])


# Add a method to log custom info
def log_custom_info(message):
    logging.log(CUSTOM_INFO, message)


# Asynchronous function for copying files
async def copy_file(file_path, dest_folder):
    """
    Copies a file to a folder corresponding to its extension.

    Args:
        file_path (Path): The path of the file to copy.
        dest_folder (Path): The destination folder for organizing files
        by extension.
    """
    try:
        # Get the file extension
        file_extension = file_path.suffix.lstrip(".").lower()
        if not file_extension:
            file_extension = "unknown"

        # Create a folder for the file extension
        dest_path = dest_folder / file_extension
        dest_path.mkdir(parents=True, exist_ok=True)

        dest_file = dest_path / file_path.name
        if dest_file.exists():
            logging.warning(
                f"File {file_path.name} already exists in {dest_path}. "
                f"Skipping copy."
            )
            return

        # Copy the file using aiofiles
        async with aiofiles.open(file_path, "rb") as src:
            async with aiofiles.open(dest_file, "wb") as dst:
                await dst.write(await src.read())

        # Log success
        logging.info(f"File {file_path.name} has been copied to {dest_path}")
    except Exception as e:
        logging.error(f"Error copying file {file_path}: {e}")


# Asynchronous function for reading a folder
async def read_folder(source_folder, dest_folder):
    """
    Recursively reads a folder and organizes its files by extension in
    the destination folder.

    Args:
        source_folder (Path): The source folder to read.
        dest_folder (Path): The destination folder for organized files.
    """
    try:
        tasks = []
        # Iterate through all files and subdirectories
        for item in source_folder.iterdir():
            if item.is_file():
                tasks.append(copy_file(item, dest_folder))
            elif item.is_dir():
                tasks.append(read_folder(item, dest_folder))
        # Execute tasks asynchronously
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error reading folder {source_folder}: {e}")


# Main function
def main():
    """
    Main function to initialize the file sorting process.
    Prompts the user for source and destination paths if not provided
    via argparse.
    """
    parser = argparse.ArgumentParser(
        description="Sort files by their extensions."
    )
    parser.add_argument(
        "--source",
        "-s",
        required=True,
        type=str,
        help="Path to the source folder."
    )
    parser.add_argument(
        "--destination",
        "-d",
        required=True,
        type=str,
        help="Path to the destination folder.",
    )
    args = parser.parse_args()

    source_folder = Path(args.source)
    sorted_folder = Path(args.destination)

    # Check if the source folder exists
    if not source_folder.is_dir():
        logging.error(
            f"Error: The source folder {source_folder} does not exist "
            f"or is not a directory."
        )
        return

    # Create the destination folder if it doesn't exist
    if not sorted_folder.exists():
        logging.info(f"Creating destination folder {sorted_folder}.")
        sorted_folder.mkdir(parents=True)

    log_custom_info("Starting file sorting...")
    asyncio.run(read_folder(source_folder, sorted_folder))
    log_custom_info("File sorting completed.")


if __name__ == "__main__":
    main()