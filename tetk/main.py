import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import queue
import threading
import logging
from inspect import currentframe as cfr
import platform

import commons
from commons import open_folder, get_latest_git_tag, classtimer
from commons import InvalidPathError
import config
from reader import FileManager
from makeppt import PptManager


def update_config_details(cfg):
    ## Added some descriptions
    cfg["software_key"] = "tetk"
    cfg["software_name"] = "Test Engr Toolkit"
    cfg["software_version"] = commons.get_version(
        cfg.log, cfg["user_config_folder"] / "version.txt"
    )
    return cfg


if getattr(sys, "frozen", False):
    # Program is a frozen exe
    # Initiates the config dictionary by loading from User's Config Folder
    # (Located in ~/Documents/~)
    cfg = config.Config(config_filename="config.yml", hard_reset=False)
    cfg.log.info("THIS PROGRAM IS FROZEN!!")
else:
    # Initiates the config dictionary (global var), with hard reset
    # User configuration folder will be erased (from ~/Documents/)
    cfg = config.Config(config_filename="config.yml", hard_reset=True)
    # writes a version info file based on git tags
    commons.writeTo_version_file(
        cfg.log,
        cfg.bundle_dir,
        filename="version.txt",
        version=get_latest_git_tag(repo_path=Path(__file__).parent.parent),
    )
    commons.copy_version_to_userConfigFolder(
        srcDir=cfg.bundle_dir, dstDir=cfg.user_config_folder
    )
    cfg.log.info("hard reset triggered")

cfg = update_config_details(cfg)
log = cfg.log


class Task(threading.Thread):
    """Class for creating task to run in parallel threads"""

    def __init__(self, master, task, name, *args):
        threading.Thread.__init__(self, target=task, args=args, name=name)
        self._stop_event = threading.Event()
        if not hasattr(master, "thread_enviar") or not master.thread_enviar.is_alive():
            master.thread_enviar = self
            self.start()


class QueueHandler(logging.Handler):
    """
    Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget

    Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class DefineTkStyle(ttk.Style):
    """Configure styles from themed TK"""

    def __init__(self, log, cfg):
        try:
            super().__init__()
            defaultBgcolor = "#ebebeb"
            self.log = log
            self.cfg = cfg
            self.theme_use("clam")

            self.configure("TFrame", background=defaultBgcolor)
            self.configure("TLabelframe", background=defaultBgcolor)
            self.configure("TLabelframe.Label", background=defaultBgcolor)

            self.configure("TCombobox")

            self.configure("TLabel", background=defaultBgcolor)
            self.configure("Header.TLabel", font=("Arial", 24, "bold"))
            self.configure("subHeader.TLabel", font=("Arial", 12, "italic"))

            self.configure(
                "TButton", background=defaultBgcolor, font=("Arial", 12, "bold")
            )
            self.configure(
                "BigButton.TButton",
                background=defaultBgcolor,
                font=("Arial", 16, "bold"),
            )
            self.configure(
                "SmallButton.TButton", background=defaultBgcolor, font=("Arial", 10)
            )

            self.configure("TRadiobutton", background=defaultBgcolor)

            self.configure(
                "BatchRecipes.TLabel", background=defaultBgcolor, font=("TkFixedFont")
            )
            self.configure(
                "BatchRecipesFn.TLabel",
                background=defaultBgcolor,
                font=("Arial", 12, "bold"),
            )

            self.configure("Footer.TLabel", font=("Arial", 12))
            self.configure("Footer.TButton", font=("Arial", 12, "bold"))

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def set_app_icon(self):
        try:
            log = self.log
            if platform.system().lower() == "windows":
                self.iconbitmap(self.cfg.wd / "icon.ico")
        except Exception as e:
            log.error(f"set icon failed;{e}")


class FrameConsole(ttk.Frame):
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, root, **kwargs):
        try:
            super().__init__(**kwargs)

            log = root.log
            self.root = root

            self.log_level = tk.StringVar()
            log_values = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            self.logbox = ttk.Combobox(
                self, textvariable=self.log_level, state="readonly", values=log_values
            )
            self.logbox.current(1)
            self.logbox.bind(
                "<<ComboboxSelected>>", lambda x: self.change_log_level(log)
            )

            # Create a ScrolledText widget
            self.scrolled_text = ScrolledText(self, height=10, width=110)
            self.scrolled_text.configure(font="TkFixedFont")
            self.scrolled_text.tag_config("DEBUG", foreground="gray")
            self.scrolled_text.tag_config("INFO", foreground="black")
            self.scrolled_text.tag_config("WARNING", foreground="orange")
            self.scrolled_text.tag_config("ERROR", foreground="red")
            self.scrolled_text.tag_config("CRITICAL", foreground="red", underline=1)

            # Create a logging handler using a queue
            self.log_queue = queue.Queue()
            self.queue_handler = QueueHandler(self.log_queue)
            formatter = logging.Formatter("%(asctime)s: %(message)s", "%H:%M")
            self.queue_handler.setFormatter(formatter)
            log.addHandler(self.queue_handler)

            self.columnconfigure(0, weight=1)
            self.columnconfigure(1, weight=39)
            ttk.Label(self, text="LoggingLevel:", anchor="center").grid(
                row=0, column=0, sticky="NSEW"
            )
            self.logbox.grid(row=0, column=1, sticky="w")
            self.scrolled_text.grid(row=1, column=0, columnspan=2, sticky="NSEW")

            log_level = log.getEffectiveLevel()
            if log_level == 10:
                self.logbox.current(0)
            elif log_level == 20:
                self.logbox.current(1)
            elif log_level == 30:
                self.logbox.current(2)
            elif log_level == 40:
                self.logbox.current(3)
            elif log_level == 50:
                self.logbox.current(4)

            # Start polling messages from the queue
            self.after(100, self.poll_log_queue)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state="normal", wrap="none")
        self.scrolled_text.insert(tk.END, msg + "\n", record.levelname)
        self.scrolled_text.yview(tk.END)
        self.scrolled_text.config(state="disabled")

    def poll_log_queue(self):
        while True:
            # Check every 100ms if there is a new message in the queue to display
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.after(100, self.poll_log_queue)

    def change_log_level(self, log):
        try:
            cfg = self.root.cfg
            myloggers, myhandlers = [], []
            log.debug("Current loggers are:")
            for k, v in log.manager.loggerDict.items():
                if not isinstance(v, logging.PlaceHolder):
                    log.debug(f"{k}: {v}")
                    [log.debug(f"{x}") for x in v.handlers]
                    myloggers.append(v)
                    for h in v.handlers:
                        myhandlers.append(h)

            if self.log_level.get() == "DEBUG":
                log.debug("Changing logging level...")
                [v.setLevel(logging.DEBUG) for v in myloggers]
                [h.setLevel(logging.DEBUG) for h in myhandlers]
                cfg["debug_mode"] = True
                log.info(f"updated to {cfg['debug_mode']=}")

            elif self.log_level.get() == "INFO":
                log.debug("Changing logging level...")
                [v.setLevel(logging.INFO) for v in myloggers]
                [h.setLevel(logging.INFO) for h in myhandlers]
                cfg["debug_mode"] = False
                log.info(f"updated to {cfg['debug_mode']=}")

            elif self.log_level.get() == "WARNING":
                log.debug("Changing logging level...")
                [v.setLevel(logging.WARNING) for v in myloggers]
                [h.setLevel(logging.WARNING) for h in myhandlers]

            elif self.log_level.get() == "ERROR":
                log.debug("Changing logging level...")
                [v.setLevel(logging.ERROR) for v in myloggers]
                [h.setLevel(logging.ERROR) for h in myhandlers]
            else:
                raise ValueError()

            for k, v in log.manager.loggerDict.items():
                if not isinstance(v, logging.PlaceHolder):
                    log.warning(f"{k}: {v}")
                    [log.warning(f"{x}") for x in v.handlers]

            log.critical(f"logger level changed to {self.log_level.get()}")

        except Exception as e:
            log.error(f"{e}")


class FrameHeader(ttk.Frame):
    """Configure Header frame in UI"""

    def __init__(self, root, **kwargs):
        try:
            cfg = root.cfg
            super().__init__(**kwargs)
            ttk.Label(self, text=cfg["software_name"], style="Header.TLabel").grid(
                row=0, column=0, sticky="sw"
            )
            ttk.Label(
                self,
                text=cfg["software_version"],
                style="subHeader.TLabel",
                anchor="s",
            ).grid(row=0, column=1, sticky="sw")

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")


class FrameFooter(ttk.Frame):
    """Configure Footer frame in UI"""

    def __init__(self, root, **kwargs):
        try:
            super().__init__(**kwargs)
            self.root = root
            self.grid_columnconfigure(0, weight=9)
            self.grid_columnconfigure(1, weight=1)
            self.left_footer = ttk.Frame(self)
            self.left_footer.grid(row=0, column=0, sticky="nsew", padx=3)
            self.right_footer = ttk.Frame(self)
            self.right_footer.grid(row=0, column=1, sticky="nsew", padx=3)

            self.lab_footer = ttk.Label(
                self.left_footer,
                text=root.footer_text,
                style="Footer.TLabel",
                anchor="sw",
            )
            self.lab_footer.pack(side=tk.LEFT)

            self.butt_clear_data = ttk.Button(
                self.right_footer,
                text="Clear data",
                style="Footer.TButton",
                command=lambda: Task(self, self.clear_data, "clear_data"),
            )
            self.butt_quit = ttk.Button(
                self.right_footer,
                text="Quit",
                style="Footer.TButton",
                command=lambda: self.root.quit_app(),
            )
            self.butt_quit.pack(side=tk.RIGHT, anchor="e")
            self.butt_clear_data.pack(side=tk.RIGHT, anchor="e")

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def clear_data(self):
        try:
            log, cfg = self.root.log, self.root.cfg
            log.info("clearing data from output folders ...")
            for fo in cfg["folders_to_clear"]:
                commons.erase_and_init(log, cfg.user_folders[fo])
            log.info("data cleared")
        except Exception as e:
            log.error(f"{cfr().f_code.co_name}();{e}")


class MainFrameA(ttk.Frame):
    """Configure Main frame in UI (Separated by Tabs in Notebook)"""

    def __init__(self, notebook, root, **kwargs):
        try:
            super().__init__(notebook, **kwargs)
            self.log, self.cfg = root.log, root.cfg
            self.root = root
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=4)
            self.frame_left = MainFrameAA(self, root, relief=tk.FLAT, width=200)
            self.frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

            self.frame_right = MainFrameAB(self, root, relief=tk.FLAT, width=800)
            self.frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")


class MainFrameAA(ttk.Frame):
    """Configure LEFT subframe of the A FRAME in UI"""

    def __init__(self, parent_frame, root, **kwargs):
        try:
            super().__init__(parent_frame, **kwargs)
            self.log = log
            self.root = root
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=4)
            self.grid_columnconfigure(2, weight=4)
            self.grid_columnconfigure(3, weight=1)
            root.inputfiles = []
            self.user_input_dict = {}

            ttk.Label(self, text="Recipe:", anchor=tk.W).grid(
                row=0, column=0, columnspan=1, sticky="nsew", padx=3, pady=3
            )
            self.entr_recipe = tk.Entry(
                self,
                textvariable=root.var_recipe_loaded_description,
                state="disabled",
                disabledforeground="black",
            )
            self.entr_recipe.grid(row=0, column=1, columnspan=3, sticky="nsew", padx=1)

            ttk.Button(
                self,
                text="Open Working DIR",
                style="TButton",
                command=lambda: open_folder(log, cfg.user_wd),
            ).grid(row=11, column=0, columnspan=4, sticky="nsew")

            ttk.Button(
                self,
                text="Open Input DIR",
                style="TButton",
                command=lambda: open_folder(log, cfg.user_folders["inpf01"]),
            ).grid(row=12, column=0, columnspan=4, sticky="nsew")

            ttk.Label(self).grid(row=40, column=1, columnspan=4, sticky="nsew", padx=1)
            ttk.Button(
                self,
                text="Run",
                style="BigButton.TButton",
                command=lambda: Task(self, self.prod_run, "prod_run"),
            ).grid(row=41, column=0, columnspan=4, sticky="nsew")

            ttk.Label(self).grid(row=50, column=1, columnspan=4, sticky="nsew", padx=1)
            ttk.Button(
                self,
                text="Run - Only lot_id plots",
                style="TButton",
                command=lambda: Task(self, self.prod_lot_id_plots, "prod_lot_id_plots"),
            ).grid(row=51, column=0, columnspan=2, sticky="nsew")
            ttk.Button(
                self,
                text="Run - Only comparison single plots",
                style="TButton",
                command=lambda: Task(self, self.prod_single_plots, "prod_single_plots"),
            ).grid(row=51, column=2, columnspan=2, sticky="nsew")

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    @classtimer
    def prod_run(self):
        try:
            log = self.root.log
            cfg = self.root.cfg

            self.root.functional_buttons["detect_images"].invoke()
            fmgr = FileManager(cfg, cfg.user_folders["inpf01"])
            data = fmgr.construct_lotPerPage()
            ppt = PptManager(cfg, cfg.user_files["ppt_template1"])
            for i, (wafer_id, wafer_imgpaths) in enumerate(data.items()):
                cfg.log.info(f"lotRun{i:03d}: {wafer_id=}; {len(wafer_imgpaths)=}")
                ppt.insert_images_wafersPerLot(wafer_id, wafer_imgpaths)

            data = fmgr.construct_singleWafers()
            ppt.insert_images_singleWaferCompare(
                df=data,
                stepsize_x=cfg["wafer_id_single_size_width_cm"],
                stepsize_y=cfg["wafer_id_single_size_width_cm"],
                fixed_width=cfg["wafer_id_single_size_width_cm"],
            )
            ppt.save_ppt()

        except Exception as e:
            log.error(f"{cfr().f_code.co_name}();{e}")

    @classtimer
    def prod_single_plots(self):
        try:
            log = self.root.log
            cfg = self.root.cfg

            self.root.functional_buttons["detect_images"].invoke()
            fmgr = FileManager(cfg, cfg.user_folders["inpf01"])
            ppt = PptManager(cfg, cfg.user_files["ppt_template1"])
            data = fmgr.construct_singleWafers()
            ppt.insert_images_singleWaferCompare(
                df=data,
                stepsize_x=cfg["wafer_id_single_size_width_cm"],
                stepsize_y=cfg["wafer_id_single_size_width_cm"],
                fixed_width=cfg["wafer_id_single_size_width_cm"],
            )
            ppt.save_ppt()

        except Exception as e:
            log.error(f"{cfr().f_code.co_name}();{e}")

    @classtimer
    def prod_lot_id_plots(self):
        try:
            log = self.root.log
            cfg = self.root.cfg

            self.root.functional_buttons["detect_images"].invoke()
            fmgr = FileManager(cfg, cfg.user_folders["inpf01"])
            data = fmgr.construct_lotPerPage()
            ppt = PptManager(cfg, cfg.user_files["ppt_template1"])
            for i, (wafer_id, wafer_imgpaths) in enumerate(data.items()):
                cfg.log.info(f"lotRun{i:03d}: {wafer_id=}; {len(wafer_imgpaths)=}")
                ppt.insert_images_wafersPerLot(wafer_id, wafer_imgpaths)
            ppt.save_ppt()

        except Exception as e:
            log.error(f"{cfr().f_code.co_name}();{e}")


class MainFrameAB(ttk.Frame):
    """Configure RIGHT subframe of the A FRAME in UI"""

    def __init__(self, parent_frame, root, **kwargs):
        try:
            super().__init__(parent_frame, **kwargs)
            self.log = root.log
            self.root = root
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=1)
            self.grid_columnconfigure(3, weight=1)

            self.user_input_text = {}

            # Create a ScrolledText widget
            ttk.Label(self, text="").grid(
                row=0, column=0, sticky="nsew", padx=3, pady=3
            )
            self.scrolled_text = ScrolledText(self, height=16, width=30, wrap="none")
            self.scrolled_text.configure(font="TkFixedFont", state="normal")
            self.scrolled_text.tag_config("HEADER", foreground="blue", underline=1)
            self.scrolled_text.tag_config("BODY", foreground="black")
            self.scrolled_text.tag_config("BODY_GREEN", foreground="green")
            self.scrolled_text.tag_config("BODY_BLUE", foreground="blue")
            self.scrolled_text.tag_config("SPECIAL", foreground="indian red")
            self.scrolled_text.tag_config("CRITICAL", foreground="red")
            self.scrolled_text.grid(
                row=1, column=0, columnspan=4, sticky="nsew", padx=3, pady=3
            )

            self.butt_detect_images = ttk.Button(
                self,
                text="Detect images",
                style="TButton",
                state="normal",
                command=lambda: Task(
                    self, self.detect_input_images, "detect_input_images"
                ),
            )
            self.butt_detect_images.grid(row=21, column=0, columnspan=1, sticky="nsew")
            root.functional_buttons["detect_images"] = self.butt_detect_images

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def display_scrolled_text(self, widget, record, tag="BODY"):
        try:
            widget.config(state="normal")
            widget.insert(tk.END, record, tag)
            widget.yview(tk.END)
        except Exception as e:
            self.root.log.error(f"{cfr().f_code.co_name}();{e}")

    def detect_input_images(self):
        try:
            log = self.root.log
            self.scrolled_text.delete("1.0", tk.END)
            fmgr = FileManager(self.root.cfg, self.root.cfg.user_folders["inpf01"])
            self.display_scrolled_text(
                self.scrolled_text,
                fmgr.pprint(text_descr="Count of Images Detected"),
            )
            log.info("detect_input_images() done")
        except Exception as e:
            log.error(f"{cfr().f_code.co_name}();{e}")


class ScrollableFrame(ttk.Frame):
    """
    Make a frame scrollable with scrollbar on the right.
    After adding or removing widgets to the scrollable frame,
    call the update() method to refresh the scrollable area.
    """

    def __init__(self, frame, width=16):
        scrollbar = tk.Scrollbar(frame, width=width)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set, height=85)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.canvas.yview)
        self.canvas.bind("<Configure>", self.__fill_canvas)

        # base class initialization
        super().__init__(frame)

        # assign this obj (the inner frame) to the windows item of the canvas
        self.windows_item = self.canvas.create_window(0, 0, window=self, anchor=tk.NW)

    def __fill_canvas(self, event):
        """Enlarge the windows item to the canvas width"""

        canvas_width = event.width
        self.canvas.itemconfig(self.windows_item, width=canvas_width)

    def update(self):
        """Update the canvas and the scrollregion"""

        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(self.windows_item), width=400)


class AppMenuBar(tk.Menu):
    """Configure the menu bar"""

    def __init__(self, root):
        try:
            self.root = root
            super().__init__(self.root)
            self.root.config(menu=self)
            self.root.option_add("*tearOff", False)

            self.file = tk.Menu(self)
            self.add_cascade(menu=self.file, label="File")

            self.licensebar = tk.Menu(self)
            self.add_cascade(menu=self.licensebar, label="License")

            self.open_cfgfolder = tk.Menu(self.file)
            self.file.add_command(
                label="Open config folder",
                command=lambda: open_folder(
                    self.root.log, self.root.cfg.user_config_folder
                ),
            )
            self.recipes_menu = tk.Menu(self.file)
            self.file.add_cascade(menu=self.recipes_menu, label="Choose recipes")
            self.root.var_recipe_loaded = tk.StringVar(value="error.yml")
            self.get_recipes()

            self.file.add_separator()
            self.var_userFiles = []
            self.file.add_command(label="Factory reset", command=self.factory_reset)
            self.file.add_separator()
            self.file.add_command(label="Quit", command=lambda: root.quit_app())
            self.licensebar.add_command(
                label="Activate license", command=self.activate_license
            )
            self.licensebar.add_command(
                label="Generate Offline token",
                command=lambda: Task(
                    self, self.make_offline_token, "make_offline_token"
                ),
            )
        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def get_recipes(self):
        try:
            log = self.root.log
            cfg = self.root.cfg
            if not cfg.user_config_folder.is_dir():
                raise InvalidPathError(f"{cfg.user_config_folder = }")

            recipes_list = [x for x in cfg.user_config_folder.glob("*.yml")]
            n = len(recipes_list)
            log.info(f"found {n} recipes.")
            if not recipes_list:
                raise Exception("no recipes found")
            else:
                for recipe in recipes_list:
                    self.recipes_menu.add_radiobutton(
                        label=recipe.name,
                        variable=self.root.var_recipe_loaded,
                        value=recipe.resolve(),
                        command=lambda: self.load_recipe(
                            self.root.var_recipe_loaded.get()
                        ),
                    )

        except Exception as e:
            log.error(f"{cfr().f_code.co_name}(); {e}")

    def load_recipe(self, recipe_f=None):
        try:
            cfg = self.root.cfg
            log = self.root.log

            if recipe_f is None:
                new_cfg = config.Config(hard_reset=False)

            else:
                recipe_path = cfg.user_config_folder / recipe_f
                if recipe_path.is_file():
                    new_cfg = config.Config(hard_reset=False, config_filename=recipe_f)
                else:
                    raise InvalidPathError(f"{recipe_path = }")

            cfg.update(new_cfg)
            cfg = update_config_details(cfg)
            self.root.var_recipe_loaded_description.set(
                f"{cfg['project_name']}_v{cfg['recipe_version']}"
            )
            cfgfile = str(cfg.user_config_file.resolve())
            log.info(f"recipe loaded. {cfgfile = }")

        except Exception as e:
            log.error(f"{cfr().f_code.co_name}(); {e}")

    def factory_reset(self):
        try:
            self.root.cfg.factory_reset()
            self.load_recipe()
        except Exception as e:
            self.root.log.error(f"{e}")

    def activate_license(self):
        try:
            self.log.info(f"{cfr().f_code.co_name}() not ready")
        except Exception as e:
            log.error(f"{cfr().f_code.co_name}(); {e=}")

    def make_offline_token(self):
        try:
            self.log.info(f"{cfr().f_code.co_name}() not ready")
        except Exception as e:
            log.error(f"{cfr().f_code.co_name}(); {e=}")


class App(tk.Tk):
    """Main app interface"""

    def __init__(self, cfg):
        try:
            super().__init__()
            self.withdraw()
            self.cfg = cfg
            self.log = cfg.log
            self.footer_text = (
                "© Copyright 2023. @jake.lim (gittf.ams-osram.info/jake.lim)"
            )
            self.app_width = 900
            self.app_height = 350
            self.functional_buttons = {}
            self.pptmanager = None
            self.data = {}
            self.var_recipe_loaded_description = tk.StringVar()

            self.resizable(width=False, height=False)
            self.configure(background="#ebebeb")
            self.title(cfg["software_key"])

            self.style = DefineTkStyle(log, cfg)

            self.menubar = AppMenuBar(self)
            self.notebook = ttk.Notebook(
                self, height=self.app_height, width=self.app_width
            )

            self.header_frame = FrameHeader(self, height=60, width=self.app_width)
            self.main_frame = MainFrameA(
                self.notebook, self, height=self.app_height, width=self.app_width
            )
            self.console_frame = FrameConsole(self, height=60, width=self.app_width)
            self.footer_frame = FrameFooter(self, height=20, width=self.app_width)

            self.notebook.add(self.main_frame, text="main")

            self.header_frame.pack(anchor="w", padx=5, pady=5, fill="both")
            self.notebook.pack(anchor="w", padx=10, pady=10, fill="both")
            self.console_frame.pack(anchor="w", padx=10, pady=3, fill="both")
            self.footer_frame.pack(anchor="w", padx=5, pady=5, fill="both")

            self.update_idletasks()
            self.deiconify()
            self.menubar.load_recipe()

        except Exception as e:
            raise Exception(f"{self.__class__.__name__};{e}")

    def update_cfg(self, tkvar, cfgkey):
        value = tkvar.get()
        self.cfg[cfgkey] = value
        self.log.info(f"cfg({cfgkey}) updated to {value} ")

    def quit_app(self):
        self.log.info("root destroy triggered by user.")
        self.quit()
        self.destroy()


def main(cfg):
    app = App(cfg)
    app.mainloop()


if __name__ == "__main__":
    main(cfg)
