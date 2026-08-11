from pathlib import Path
import shutil


class FileTools:
    """Safe local file-management tools."""

    def create_file(self, path: str, content: str = "") -> str:
        """Create a new file."""

        file_path = Path(path).expanduser()

        try:
            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path.write_text(
                content,
                encoding="utf-8",
            )

            return f"Created file: {file_path}"

        except Exception as error:
            return f"Unable to create file: {error}"

    def search_file(self, directory: str, filename: str) -> str:
        """Search for a file by name."""

        root = Path(directory).expanduser()

        if not root.exists():
            return f"Directory does not exist: {root}"

        matches = []

        try:
            for path in root.rglob(filename):
                if path.is_file():
                    matches.append(str(path))

                if len(matches) >= 20:
                    break

            if not matches:
                return f"No file named '{filename}' was found."

            return "\n".join(matches)

        except Exception as error:
            return f"Unable to search files: {error}"

    def copy_file(self, source: str, destination: str) -> str:
        """Copy a file."""

        source_path = Path(source).expanduser()
        destination_path = Path(destination).expanduser()

        try:
            destination_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                source_path,
                destination_path,
            )

            return f"Copied {source_path} to {destination_path}"

        except Exception as error:
            return f"Unable to copy file: {error}"

    def move_file(self, source: str, destination: str) -> str:
        """Move a file."""

        source_path = Path(source).expanduser()
        destination_path = Path(destination).expanduser()

        try:
            destination_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.move(
                str(source_path),
                str(destination_path),
            )

            return f"Moved {source_path} to {destination_path}"

        except Exception as error:
            return f"Unable to move file: {error}"

    def rename_file(self, source: str, new_name: str) -> str:
        """Rename a file."""

        source_path = Path(source).expanduser()
        destination = source_path.with_name(new_name)

        try:
            source_path.rename(destination)

            return f"Renamed file to {destination}"

        except Exception as error:
            return f"Unable to rename file: {error}"
