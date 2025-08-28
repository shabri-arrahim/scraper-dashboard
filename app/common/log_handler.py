import time
import logging

from pathlib import Path
from typing import Optional, List

from app.core.config import settings


class ScriptLogHandler:
    def __init__(self, script_name: str, append_mode: bool = True):
        self.script_name = script_name
        self.append_mode = append_mode

        # Create consistent log file name (no timestamp)
        self.log_file = settings.LOGS_DIR / f"{script_name}.log"

        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Clear file if not in append mode
        if not append_mode:
            self.clear_log_file()

        self._setup_logging()

    def _setup_logging(self):
        """Set up file logging with unique logger per instance"""
        # Create unique logger name to avoid conflicts between instances
        logger_name = f"script_{self.script_name}"
        self.logger = logging.getLogger(logger_name)

        # Only set up if not already configured
        if not self.logger.handlers:
            # Use append mode by default, or write mode if specified
            mode = "a" if self.append_mode else "w"
            self.file_handler = logging.FileHandler(self.log_file, mode=mode)
            self.file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(levelname)s - [Job:%(job_id)s] %(message)s"
                )
            )

            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(self.file_handler)

    def write(self, message: str, level: str = "INFO"):
        """Write log message to file with job_id context"""
        # Add job_id to the log record for formatting
        log_record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, level.upper(), logging.INFO),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        # log_record.job_id = self.job_id

        self.logger.handle(log_record)

        self.rotate_log_file(max_size_mb=20)

    def read_log_file(self) -> str:
        """Read the entire log file content"""
        try:
            return self.log_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except Exception as e:
            return f"Error reading log file: {e}"

    def read_log_lines(self, num_lines: Optional[int] = None) -> list[str]:
        """Read log file lines, optionally limiting to last N lines"""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if num_lines is not None:
                return lines[-num_lines:] if len(lines) >= num_lines else lines
            return lines
        except FileNotFoundError:
            return []
        except Exception as e:
            return [f"Error reading log file: {e}"]

    def clear_log_file(self):
        """Clear the log file content"""
        try:
            self.log_file.write_text("", encoding="utf-8")
        except Exception as e:
            print(f"Error clearing log file: {e}")

    def delete_log_file(self):
        """Delete the log file"""
        try:
            if self.log_file.exists():
                self.log_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting log file: {e}")
            return False

    def get_log_file_path(self) -> Path:
        """Get the path to the log file"""
        return self.log_file

    def get_log_file_size(self) -> int:
        """Get log file size in bytes"""
        try:
            return self.log_file.stat().st_size if self.log_file.exists() else 0
        except Exception:
            return 0

    def rotate_log_file(self, max_size_mb: int = 10):
        """Rotate log file if it exceeds max size"""
        max_size_bytes = max_size_mb * 1024 * 1024

        if self.get_log_file_size() > max_size_bytes:
            # Create backup
            backup_file = self.log_file.with_suffix(".log.old")
            if backup_file.exists():
                backup_file.unlink()  # Remove old backup

            # Move current to backup
            self.log_file.rename(backup_file)

            # Create new empty file
            self.log_file.touch()

            # Re-setup logging to use new file
            self.close()
            self._setup_logging()

    def close(self):
        """Clean up handlers"""
        if hasattr(self, "file_handler"):
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

    def flush(self):
        """Required for compatibility with subprocess output"""
        if hasattr(self, "file_handler"):
            self.file_handler.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LogFileReader:
    """Lightweight class for reading log files without creating logger instances"""

    def __init__(self, script_name: str):
        self.script_name = script_name
        self.log_file = settings.LOGS_DIR / f"{script_name}.log"

    def read_log_file(self) -> str:
        """Read the entire log file content"""
        try:
            return (
                self.log_file.read_text(encoding="utf-8")
                if self.log_file.exists()
                else ""
            )
        except Exception as e:
            return f"Error reading log file: {e}"

    def read_log_lines(self, num_lines: Optional[int] = None) -> List[str]:
        """Read log file lines, optionally limiting to last N lines"""
        try:
            if not self.log_file.exists():
                return []

            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if num_lines is not None:
                return lines[-num_lines:] if len(lines) >= num_lines else lines
            return lines
        except Exception as e:
            return [f"Error reading log file: {e}"]

    def tail_log_file(self, num_lines: int = 20) -> List[str]:
        """Get the last N lines (like tail command)"""
        return self.read_log_lines(num_lines)

    def search_log_lines(self, pattern: str, case_sensitive: bool = False) -> List[str]:
        """Search for lines containing a pattern"""
        try:
            if not self.log_file.exists():
                return []

            lines = self.read_log_lines()
            if not case_sensitive:
                pattern = pattern.lower()
                return [line for line in lines if pattern in line.lower()]
            else:
                return [line for line in lines if pattern in line]
        except Exception as e:
            return [f"Error searching log file: {e}"]

    def get_log_file_info(self) -> dict:
        """Get information about the log file"""
        try:
            if not self.log_file.exists():
                return {
                    "exists": False,
                    "path": str(self.log_file),
                    "size_bytes": 0,
                    "size_mb": 0,
                    "line_count": 0,
                }

            stat = self.log_file.stat()
            line_count = len(self.read_log_lines())

            return {
                "exists": True,
                "path": str(self.log_file),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "line_count": line_count,
                "modified_time": time.ctime(stat.st_mtime),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_log_files_for_script(self) -> List[Path]:
        """Get all log files for this script (including rotated ones)"""
        try:
            log_dir = settings.LOGS_DIR
            pattern = f"{self.script_name}*.log*"
            return list(log_dir.glob(pattern))
        except Exception:
            return []

    def delete_log_file(self) -> bool:
        """Delete the main log file"""
        try:
            if self.log_file.exists():
                self.log_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting log file: {e}")
            return False

    def delete_all_log_files(self) -> int:
        """Delete all log files for this script including rotated ones"""
        deleted_count = 0
        try:
            log_files = self.get_log_files_for_script()
            for log_file in log_files:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {log_file}: {e}")
            return deleted_count
        except Exception as e:
            print(f"Error deleting log files: {e}")
            return 0
