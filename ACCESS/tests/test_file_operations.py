import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from ui.file_operations import duplicate_destination, format_file_size, is_hidden, reveal_command


class FileOperationsTests(unittest.TestCase):
    def test_file_size_formatting(self):
        self.assertEqual(format_file_size(0), "0 B")
        self.assertEqual(format_file_size(1023), "1023 B")
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.0 MB")

    def test_negative_size_is_bounded(self):
        self.assertEqual(format_file_size(-1), "0 B")

    def test_native_reveal_commands(self):
        path = Path("/tmp/example.txt")
        self.assertEqual(reveal_command(path, "Darwin"), ["open", "-R", str(path)])
        self.assertEqual(reveal_command(path, "Windows"), ["explorer", f"/select,{path}"])
        self.assertEqual(reveal_command(path, "Linux"), ["xdg-open", str(path.parent)])

    def test_duplicate_name_avoids_conflicts(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "notes.txt"
            source.touch()
            self.assertEqual(duplicate_destination(source).name, "notes copy.txt")
            (Path(directory) / "notes copy.txt").touch()
            self.assertEqual(duplicate_destination(source).name, "notes copy 2.txt")

    def test_dotfiles_are_hidden_cross_platform(self):
        self.assertTrue(is_hidden(Path(".env")))
        self.assertFalse(is_hidden(Path("notes.txt")))


if __name__ == "__main__":
    unittest.main()
