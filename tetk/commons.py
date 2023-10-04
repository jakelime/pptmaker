import logging
import logging.config
import os
from pathlib import Path
import time
import inspect
from inspect import currentframe as cfr
import platform
import subprocess
import shutil
import sys
import re


def get_latest_git_tag(repo_path: Path = None, err_code: str = "versionError") -> str:
    """function to use GitPython to get a list of tags

    :param repo_path: path where .git resides in
    :type repo_path: pathlib.Path
    :return: latest git tag
    :rtype: str
    """
    results = ""
    try:
        sp = subprocess.run(
            ["git", "describe", "--tag"],
            check=True,
            timeout=5,
            capture_output=True,
            encoding="utf-8",
        )
        results = sp.stdout.strip()

        if not results:
            results = err_code

    except Exception:
        pass

    finally:
        return results


def get_time(datetimestrformat: str = "%Y%m%d_%H%M%S"):
    """
    Returns the datetime string at the time of function call
    :param datetimestrformat: datetime string format, defaults to "%Y%m%d_%H%M%S"
    :type datetimestrformat: str, optional
    :return: datetime in string format
    :rtype: str
    """
    return time.strftime(datetimestrformat, time.localtime(time.time()))


class InvalidPathError(Exception):
    """Custom Exception Error class for invalid path"""

    def __init__(self, message, *args):
        self.message = f"InvalidPathError({message})"  # without this you may get DeprecationWarning
        # allow users initialize misc. arguments as any other builtin Error


def get_path_bundles():
    if getattr(sys, "frozen", False):
        pathcwd = os.path.dirname(sys.executable)
    elif __file__:
        pathcwd = os.path.dirname(__file__)
    pathbundles = os.path.join(pathcwd, "bundles")
    return Path(pathbundles)


def chgdict_changekeyvalues(
    log: logging.Logger, d: dict, required_key: str, new_value, case_sensitive=False
):
    for k, v in d.items():
        if isinstance(v, dict):
            chgdict_changekeyvalues(log, v, required_key, new_value)

        else:
            if isinstance(v, str):
                if not case_sensitive:
                    if v.lower() == required_key.lower():
                        d[k] = new_value

                else:
                    if v == required_key:
                        d[k] = new_value
    return d


def classtimer(func):
    def wrapper(ref_self, *args, **kwargs):
        log = ref_self.log
        # print(f"log={log}; *args={args}, **kwargs={kwargs}")
        t0 = time.perf_counter()
        func(ref_self, *args, **kwargs)
        log.info(f"[{func.__name__}] elapsed_time = {(time.perf_counter()-t0):.4f}s")

    return wrapper


def open_folder(log, path):
    try:
        path = Path(path)
        if path.is_dir():
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        else:
            raise Exception(f"path({path=}) is not a valid dir")
        log.info(f"Open folder success. [{os.sep}{path.name}]")
    except Exception as e:
        raise Exception(f"{cfr().f_code.co_name}();{e}")


def output(
    log: logging.Logger,
    fpath: Path,
    pathlevels: int = 1,
    space: int = 1,
    logleveldebug: bool = False,
):
    try:
        if isinstance(fpath, Path):
            parent_folder = fpath.parent
            fname = fpath.name
            filesuffix = fpath.suffix
            parents_splitted = parent_folder.parts
        else:
            parent_folder, fname = os.path.split(fpath)
            filesuffix = f".{fname.split('.')[-1]}"
            parents_splitted = parent_folder.split(os.sep)

        space *= " "

        if pathlevels == 0:
            pathprint = f"{os.sep*2}"
        else:
            pathprint = os.sep.join(parents_splitted[-1 * pathlevels :])
            pathprint = f"{os.sep*2}{pathprint}{os.sep}"

        if not logleveldebug:
            log.info(f"{space}>>{filesuffix} created. {pathprint}{fname}")
        else:
            log.debug(f"{space}>>{filesuffix} created. {pathprint}{fname}")

    except Exception as e:
        raise Exception(f"{inspect.currentframe().f_code.co_name}(), {e}")


def filter_os_safe_filename(value):
    return re.sub(r"[^A-Za-z0-9 ._-]+", "", value)


def erase_and_init(log, path):
    try:
        if not isinstance(path, Path):
            path = Path(path)
        if path.is_dir():
            try:
                shutil.rmtree(path)
                log.info(f"data deleted({path.name=}).")
            except Exception as e:
                raise e

        path.mkdir()
        log.info(f"initialised({path.name})")
        return True

    except Exception as e:
        raise Exception(f"{cfr().f_code.co_name}();{e}")


def filter_strings(value):
    outvalue = re.sub(r"[^A-Za-z0-9 _;-]+", "", value)
    outvalue = outvalue.strip()
    return outvalue


def copy_version_to_userConfigFolder(
    srcDir: Path, dstDir: Path, filename: str = "version.txt"
):
    src = srcDir / filename
    dst = dstDir / filename
    try:
        shutil.copy2(src, dst)
    except FileNotFoundError:
        raise FileNotFoundError(f"Copy src=~/{srcDir.name}/{filename}")
    except PermissionError:
        raise PermissionError(f"Copy dst=~/{dst.parent}/{dst.name}")
    except Exception as e:
        raise e


def writeTo_version_file(
    log: logging.Logger,
    parent_dir: Path,
    filename: str = "version.txt",
    version: str = "versionErr",
):
    version_file = parent_dir / filename
    try:
        with open(version_file, "w") as fm:
            fm.write(version)
        log.info(f"version updated to {version}")
        return True
    except IOError:
        log.error("IOError: software version update failed")
    finally:
        return False


def get_version(log: logging.Logger, version_file: Path):
    try:
        with open(version_file, "r") as fm:
            version = fm.readline()
        return version
    except IOError:
        log.warning(f"{version_file=}")
        log.error(f"IOError: unable to access {version_file=}")
        return "versionErr"


def setup_stream_logger(loglevel=logging.INFO):
    logger = logging.getLogger(__name__)

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(loglevel)

    # Create formatters and add it to handlers
    # or "[%(asctime)s]%(levelname)-8s: %(message)s", "%y-%j %H:%M:%S"
    c_format = logging.Formatter("%(levelname)-8s: %(message)s")
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.setLevel(loglevel)
    return logger


if __name__ == "__main__":
    log = setup_stream_logger()

    cwd = Path(__file__)
    bundles_path = cwd.parent / "bundles"

    writeTo_version_file(
        log, bundles_path, filename="version.txt", version=get_latest_git_tag()
    )
    version = get_version(log, bundles_path / "version.txt")
    print(f"get {version=}")
