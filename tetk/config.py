import sys
import os
import inspect
import yaml
import shutil
from pathlib import Path
import commons
import logging
from logging.handlers import RotatingFileHandler
from inspect import currentframe as cfr


class Config(dict):
    """
    Creates the configuration dict to allow user different configurations.

    :param hard_reset: Set True to reintialise the user configuration folder, defaults to True
    :type hard_reset: Bool, optional
    :param bundle_config_file: Original factory default name of config file name, defaults to 'config.yml'
    :type bundle_config_file: str, optional
    :param config_filename: Config file intended to be loaded by user, defaults to 'config.yml'
    :type config_filename: str, optional
    :return: configurations loaded from user configuration file config.yml
    :rtype: dict
    """

    def __init__(
        self,
        *,
        hard_reset=False,
        config_filename="config.yml",
        bundle_config_file="config.yml",
    ):

        # This code snippet will fix MacOS pyinstaller .app from crashing immediately
        if getattr(sys, "frozen", False):
            current_filepath = os.path.dirname(sys.executable)
        else:
            current_filepath = str(os.path.dirname(__file__))
        current_filepath = Path(
            current_filepath
        )  # gets the current_filepath, works even if frozen
        self.wd = current_filepath  # sets the working_dir, works even if frozen

        self.user_config_filename = config_filename
        self.bundle_dir = self.wd / "bundles"
        self.bundle_config_file = self.bundle_dir / bundle_config_file

        loaded_cfg = self.load_yaml(self.bundle_config_file)
        self.update(loaded_cfg)
        self.setup_logger()
        log = self.log

        self.paths_init(hard_reset=hard_reset)
        log.info("default configuration initialised.")

        self.user_config_file = self.user_config_folder / self.user_config_filename
        log.info(f"user input {config_filename=}")
        user_cfg = self.load_yaml(self.user_config_file)
        self.update(user_cfg, hard_reset=False)
        log.info(f"user configuration loaded. {self.user_config_file.name=}")

    def setup_logger(self, name="tetk", default_loglevel=logging.INFO):
        """
        Function to initialise logging function.
        Logs to both console stdout and also a log file
        Log file will be logged to user working directory, defaults to My Documents/_TOOLS_tetk/tetk.log

        :param name: Name of the log file, f"{name}.log"
        :type name: str
        :return: None
        """

        logger = logging.getLogger(__name__)

        if logger.hasHandlers():
            logger.warning(
                f"existing logger detected, skipping {cfr().f_code.co_name}()"
            )

        else:
            self.user_mydocuments = Path(os.path.expanduser(self.user_OS_default))
            self.user_wd = self.user_mydocuments / self.user_working_dir_name
            self.user_logfile = self.user_wd / f"{name}.log"

            if not self.user_logfile.is_file():
                self.user_logfile.parent.mkdir(parents=True, exist_ok=True)
                with self.user_logfile.open("w", encoding="utf-8") as f:
                    f.write("")

            # Create handlers
            c_handler = logging.StreamHandler()
            # f_handler = logging.FileHandler()
            f_handler = RotatingFileHandler(
                self.user_logfile, maxBytes=5_242_880, backupCount=10
            )
            c_handler.setLevel(default_loglevel)
            f_handler.setLevel(default_loglevel)

            # Create formatters and add it to handlers
            c_format = logging.Formatter("%(levelname)-8s: %(message)s")
            f_format = logging.Formatter(
                "[%(asctime)s]%(levelname)-8s: %(message)s", "%y-%j %H:%M:%S"
            )
            c_handler.setFormatter(c_format)
            f_handler.setFormatter(f_format)

            # Add handlers to the logger
            logger.addHandler(c_handler)
            logger.addHandler(f_handler)
            logger.setLevel(default_loglevel)

        self.log = logger

    def paths_init(self, hard_reset=False):
        """
        Initialises path read from the config.yml into pathlib.Path
        Creates the working directories in user's working directory, defaults to My Documents/tetk
        Creates the configuration folder in user's working directory, defaults to My Documents/tetk/_configurations
        Copies factory default config files to user configuration folder

        :param hard_reset:  Set True to delete the user configuration folder then restore using factory defaults, defaults to True
        :type hard_reset: str
        :return: None
        """

        log = self.log
        self.created_files = []
        self.created_dirs = []

        self.user_mydocuments = Path(os.path.expanduser(self.user_OS_default))
        self.user_wd = self.user_mydocuments / self.user_working_dir_name
        if not self.user_wd.is_dir():
            self.user_wd.mkdir(parents=True, exist_ok=True)
            self.created_dirs.append(True)

        self.user_config_folder = self.user_wd / "_configurations"
        if hard_reset:
            try:
                if self.user_config_folder.is_dir():
                    shutil.rmtree(self.user_config_folder)
                    log.warning(f"hard reset done. removed {self.user_config_folder=}")
            except Exception as e:
                raise Exception(
                    f"hard reset, os.remove failed({self.user_config_folder=}; {e=}"
                )

        if not self.user_config_folder.is_dir():
            self.user_config_folder.mkdir(parents=True, exist_ok=True)
            log.info(f"created {self.user_config_folder=}")
            self.created_dirs.append(True)

        self.user_config_file = self.user_config_folder / self.bundle_config_file.name
        if not self.user_config_file.is_file():
            try:
                shutil.copy2(self.bundle_config_file, self.user_config_file)
                log.info(f"created {self.user_config_file=}")
                self.created_files.append(True)
            except Exception:
                raise Exception(
                    f"CRITICAL copy failed({self.bundle_config_file=}, {self.user_config_file=}); {e=}"
                )

        self.user_files = {}
        if self.files_key_names is not None:
            for file_key, filename in self.files_key_names.items():
                src_file = self.bundle_dir / filename
                dst_file = self.user_config_folder / filename
                self.user_files[file_key] = dst_file
                if not dst_file.is_file():
                    try:
                        shutil.copy2(src_file, dst_file)
                        log.info(f"created {dst_file=}")
                        self.created_files.append(True)
                    except FileNotFoundError:
                        log.error(f"Init: FileNotFoundError({str(src_file.resolve())})")
                    except Exception as e:
                        log.error(f"copy failed({src_file=}, {dst_file=}); {e=}")

        try:
            commons.copy_version_to_userConfigFolder(srcDir=self.bundle_dir, dstDir=self.user_config_folder)
            self.created_files.append(True)
        except Exception as e:
            log.error(e)


        self.user_folders = {}
        if self.folders_key_names is not None:
            for folder_key, foldername in self.folders_key_names.items():
                folderpath = self.user_wd / foldername
                self.user_folders[folder_key] = folderpath
                if not folderpath.is_dir():
                    folderpath.mkdir(parents=True, exist_ok=True)
                    log.info(f"created {self.user_config_folder=}")
                    self.created_dirs.append(True)

        log.info(f"created {sum(self.created_dirs)} dirs.")
        log.info(f"created {sum(self.created_files)} files.")
        log.info("paths initialised.")

    def factory_reset(self):
        """
        Backups the entire working folder by renaming the user working dir
        Re-initialise by creating new configuration files and foldrs from factory defaults
        """
        try:
            log = self.log
            log.warning(f"initiating factory reset ...")
            new_path = (
                self.user_wd.parent
                / f"{self.user_wd.name}_backedup_{commons.get_time()}"
            )
            os.rename(self.user_wd, new_path)
            log.info(f"backed up old working dir to {new_path.name}")
            self.__init__()

        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}();{e}")

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        dict_str = "\n".join([f"{k}: {v}" for k, v in self.items()])
        return dict_str

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def load_yaml(self, filepath="config.yml"):
        """loads the yaml files"""
        filepath = Path(filepath)
        assert filepath.is_file(), f"unable to load yaml, {filepath=}"
        with open(filepath, "r") as stream:
            try:
                loaded_cfg = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                try:
                    self.log.error(e)
                except Exception:
                    print(e)
        return loaded_cfg

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)


def main():
    cfg = Config(config_filename="config.yml")
    log = cfg.log
    log.info(cfg)


if __name__ == "__main__":
    main()
