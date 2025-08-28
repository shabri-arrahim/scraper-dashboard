import aiofiles.os as async_os
import fnmatch


async def iter_glob(path, pattern):
    dirs = await async_os.scandir(path)
    for entry in dirs:
        if fnmatch.fnmatch(entry.name, pattern):
            yield entry
