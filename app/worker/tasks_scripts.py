import os
import signal
import asyncio
import subprocess
import logging

from typing import Callable, Optional, Any
from celery import Task

from app.common.log_handler import ScriptLogHandler
from app.jobs.models import Job
from app.scripts.models import Script
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services import telegram

logger = logging.getLogger(__name__)


class NoRetryTask(Task):
    max_retries = 0


@celery_app.task(bind=True, base=NoRetryTask)
def run_script(
    self,
    job_id: int,
    script_id: str,
    **kwargs,
):
    """Celery task to run a Python script"""
    asyncio.run(_run_script_async(job_id=job_id, script_id=script_id, **kwargs))


@celery_app.task(bind=True, base=NoRetryTask)
def stop_script(self, job_id: int, **kwargs):
    """Celery task to stop a running script"""
    asyncio.run(_stop_script_async(job_id=job_id, **kwargs))


async def _read_stream(
    stream: asyncio.subprocess.Process,
    callback: Optional[Callable[..., Any]],
) -> None:
    output_lines = []
    last_output_time = settings.TIME_NOW()
    max_silence_duration = 600  # 10 minutes of no output = potential hang

    while True:
        try:

            if stream.returncode is not None:
                break

            line: bytes = await asyncio.wait_for(
                stream.stdout.readline(), timeout=60  # Max wait is 1 minutes
            )

            if not line:
                break

            last_output_time = settings.TIME_NOW()
            streamed_line = line.decode().strip()
            output_lines.append(streamed_line)

            callback(streamed_line, level="INFO")

            match streamed_line:
                case s if "TimeoutError" in s:
                    callback("⚠️  Playwright timeout detected", level="WARNING")
                case s if "Browser closed" in s:
                    callback("ℹ️  Browser session ended", level="INFO")

        except asyncio.TimeoutError as e:
            silence_duration = (settings.TIME_NOW() - last_output_time).total_seconds()
            if silence_duration > max_silence_duration:
                callback(
                    f"⚠️  No output for {silence_duration:.0f}s, script may be hanging",
                    level="WARNING",
                )
                break
            continue

    return output_lines


async def _run_script_async(job_id: int, script_id: str, **kwargs) -> None:
    async with AsyncSessionLocal() as db:
        process = None
        try:
            script = await Script.get_by_id(session=db, script_id=script_id)
            job = await Job.get_by_id(session=db, job_id=job_id)
            script_path = settings.SCRIPTS_DIR / f"{script.name}.py"

            if not job:
                raise ValueError(f"Can't find job with ID: {job_id}")

            extra_env = {**os.environ, "PYTHONUNBUFFERED": "1"}

            if os.name == "nt":
                process = await asyncio.create_subprocess_exec(
                    "python",
                    "-u",
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=extra_env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    cwd=settings.SCRIPTS_DIR,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    "python",
                    "-u",
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=extra_env,
                    preexec_fn=os.setsid(),
                    cwd=settings.SCRIPTS_DIR,
                )

            with ScriptLogHandler(script_name=script.name) as script_log_handler:
                output_lines = await _read_stream(process, script_log_handler.write)
                script.log_file = str(script_log_handler.log_file.name)
                await db.commit()

            return_code = await process.wait()
            if return_code == 0:
                status = "completed"
                logger.info(
                    f"✅ Script completed successfully. Processed {len(output_lines)} log lines."
                )
                await telegram.send_message(
                    f"✅ Script completed successfully. Processed {len(output_lines)} log lines.",
                    settings.TELEGRAM_CHAT_ID,
                )
            else:
                status = "failed"
                error_msg = (
                    f"❌ Playwright script failed with return code {return_code}"
                )
                logger.error(error_msg)

                # Check for common Playwright errors in output
                output_text = "\n".join(output_lines[-20:])  # Last 20 lines

                # Telegram Error Message
                telegram_error_meesage = ""
                idx = len(output_text) - 1
                while idx > 0:
                    telegram_error_meesage = (
                        output_text[idx].strip() + " " + telegram_error_meesage
                    )
                    if (
                        len(f"{error_msg}:\n{telegram_error_meesage}")
                        >= settings.TELEGRAM_MAX_MESSAGE_CHAR
                    ):
                        break
                    idx -= 1

                logger.info(f"{len(telegram_error_meesage)=}")
                logger.info(f"{telegram_error_meesage=}")
                await telegram.send_message(
                    f"{telegram_error_meesage}",
                    settings.TELEGRAM_CHAT_ID,
                )
                match output_text:
                    case s if "TimeoutError" in s:
                        logger.info(
                            "💡 Tip: Consider increasing timeouts or adding waits"
                        )
                        await telegram.send_message(
                            f"TimeoutError:\n💡 Tip: Consider increasing timeouts or adding waits",
                            settings.TELEGRAM_CHAT_ID,
                        )
                    case s if "Browser closed" in s:
                        logger.info(
                            "💡 Tip: Browser may have crashed, check memory usage",
                        )
                        await telegram.send_message(
                            f"Browser closed:\n💡 Tip: Browser may have crashed, check memory usage",
                            settings.TELEGRAM_CHAT_ID,
                        )
                    # case _:
                    #     await log_handler.write(
                    #         output_text, level="INFO", db=db
                    #     )

            job.status = status
            job.end_time = settings.TIME_NOW()
            await db.commit()

            return {
                "status": status,
                "return_code": return_code,
                "lines_processed": len(output_lines),
            }

        except Exception as e:
            error_msg = str(e)

            # Ensure process cleanup
            if process and process.returncode is None:
                logger.info(f"Execute Kill process: {str(process.pid)}")
                try:
                    if os.name == "nt":
                        # Kill entire process tree on Windows
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                            capture_output=True,
                        )
                    else:
                        pgid = os.getpgid(process.pid)
                        current_pgid = os.getpgid(current_pid)

                        if pgid != current_pgid:
                            os.killpg(pgid, signal.SIGKILL)
                        else:
                            # Fallback to killing just the process
                            os.kill(process.pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass  # Process already dead

            # Update job status
            if "job" in locals() and job:
                job.status = "failed"
                job.end_time = settings.TIME_NOW()
                job.error_message = error_msg
                await db.commit()

            logger.info(f"💥 Fatal error: {error_msg}")

            await telegram.send_message(
                f"💥 Fatal error: {error_msg}", settings.TELEGRAM_CHAT_ID
            )

            raise

        finally:
            pass


async def _stop_script_async(job_id: int, **kwargs):
    async with AsyncSessionLocal() as db:
        try:
            job = await Job.get_by_id(session=db, job_id=job_id)

            if not job or not job.pid:
                raise ValueError(f"Job {job_id} not found or has no PID")

            try:
                if os.name == "nt":
                    # Windows - kill entire process tree (includes browser processes)
                    stop_process = await asyncio.create_subprocess_exec(
                        "taskkill",
                        "/F",
                        "/T",
                        "/PID",
                        str(job.pid),
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    await stop_process.wait()
                else:
                    # Unix - kill process group (includes browser processes)
                    try:
                        # First try graceful termination
                        os.killpg(os.getpgid(job.pid), signal.SIGTERM)
                        await asyncio.sleep(5)  # Give it 5 seconds

                        # Then force kill if still running
                        try:
                            os.killpg(os.getpgid(job.pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Already terminated
                    except ProcessLookupError:
                        pass

                logger.info(
                    "🛑 Playwright script and browser processes stopped by user",
                )
                await telegram.send_message(
                    f"🛑 Playwright script and browser processes stopped by user",
                    settings.TELEGRAM_CHAT_ID,
                )

            except Exception as e:
                logger.warning(
                    f"⚠️  Error during stop: {e}, process may have already finished",
                )
                await telegram.send_message(
                    f"⚠️  Error during stop: {e}, process may have already finished",
                    settings.TELEGRAM_CHAT_ID,
                )

            # Update job status
            job.status = "stopped"
            job.end_time = settings.TIME_NOW()
            await db.commit()

        except Exception as e:
            if "job" in locals() and job:
                job.status = "failed"
                job.end_time = settings.TIME_NOW()
                job.error_message = str(e)
                await db.commit()
            raise
