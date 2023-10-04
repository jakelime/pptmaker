from collections import namedtuple
import pandas as pd
from pathlib import Path
from commons import get_time
# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)


class DataInfo(dict):
    def __init__(self):
        super().__init__()

    def add_data(self, *args):
        for arg in args:
            if type(arg) is dict:
                self.update(arg)
            elif type(arg) is list:
                data_ = {f"id{len(self.keys())+1}": arg}
                self.update(data_)


class FileManager:
    """
    FileManager

    :param folderpath: Accepts a input folder dir
    :type folderpath: pathlib.Path
    """

    def __init__(self, cfg: dict, folderpath: Path, fileext: str = "*.png"):
        self.cfg = cfg
        self.log = cfg.log
        self.fileext = fileext
        assert folderpath.is_dir(), f"{folderpath.is_dir() = }"
        self.folderpath = folderpath

        self.FileTableStructure = namedtuple("Data", "foldername filename filepath")
        self.get_filetable(self.folderpath)

    def get_filetable(self, folderpath: Path) -> pd.DataFrame:
        self.log.debug(f"input folder is {folderpath.resolve()}")

        datalist = []
        for filepath in folderpath.rglob(self.fileext):
            datalist.append(
                self.FileTableStructure(
                    foldername=filepath.parent.name,
                    filename=filepath.name,
                    filepath=filepath,
                )
            )

        df = pd.DataFrame(datalist)
        if df.empty:
            raise ValueError(
                "empty dataframe. is `input_validation` configured correctly?"
            )
        df = df[df["foldername"].isin(self.cfg["input_validation"])]
        df["throwaway"] = df["filename"].apply(lambda x: len(x.split("_")))
        df = df[df["throwaway"] < self.cfg["throwaway_threshold"]]
        df["temp"] = df["foldername"].apply(lambda x: x.replace("C", ""))
        df["temp"] = pd.to_numeric(df["temp"], downcast="integer", errors="coerce")
        df["product_id"] = df["filename"].apply(lambda x: x.split("_")[0])
        df["lot_id"] = df["filename"].apply(lambda x: x.split("_")[1])
        df["wafer_id"] = df["filename"].apply(lambda x: x.split("_")[2].split("-")[1])

        self.df = df

    def construct_lotPerPage(self) -> dict[str, list]:

        data = DataInfo()
        folders = self.df.foldername.unique()
        lot_ids = self.df.lot_id.unique()

        for folder in folders:
            for lot_id in lot_ids:
                df = (
                    self.df[(self.df.foldername == folder) & (self.df.lot_id == lot_id)]
                    .sort_values("wafer_id")
                    .reset_index(drop=True)
                )
                data.add_data({f"{folder}::{lot_id}": df.filepath.to_list()})

        return data

    def construct_singleWafers(self) -> pd.DataFrame:
        df = self.df.pivot(
            index=["lot_id", "wafer_id"], columns="foldername", values="filepath"
        )
        if self.cfg['debug_mode']:
            outname = f"construct_singleWafers-{get_time()}.csv"
            outpath = self.cfg['user_folders']['outf02'] / outname
            df.to_csv(outpath)
            self.log.info(f"debug > created //{outpath.parent.name}/{outpath.name}")

        return df.sort_index()

    def pprint(self, dfin=None, text_descr: str = ""):

        ## Prints less columns
        # df = dfin[
        #     ["foldername", "filename", "throwaway", "product_id", "lot_id", "wafer_id"]
        # ]
        if dfin is None:
            df = self.df
        else:
            df = dfin.copy()

        df = pd.pivot_table(
            df,
            columns=["foldername"],
            index=["lot_id"],
            values="filename",
            aggfunc="count",
        )
        print(df)
        return f"{text_descr}: \n{df.to_string()}"

    def sortby_lotPerPage(self):
        return self.df.sort_values(
            ["product_id", "temp", "lot_id", "wafer_id"]
        ).reset_index(drop=True)

    def sortby_tempPerPage(self):
        return self.df.sort_values(
            ["product_id", "lot_id", "wafer_id", "temp"]
        ).reset_index(drop=True)


def run(cfg: dict) -> list[pd.DataFrame]:

    fmgr = FileManager(cfg, cfg.user_folders["inpf01"])
    if fmgr.construct_lotPerPage() is not None:
        cfg.log.info("FileManager construction sucessful.")

    # fmgr.pprint()

    data = fmgr.construct_singleWafers()
    print(data)
    # [print(f"{k}: {len(v)}") for k, v in data.items()]


if __name__ == "__main__":

    pd.set_option("display.max_columns", 15)
    pd.set_option("display.max_rows", 50)
    pd.set_option("display.width", None)

    from main import cfg

    run(cfg)
