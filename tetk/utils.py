from pathlib import Path
import pandas as pd


class PathFinder:
    def __init__(self, cwd: None | Path = None, resources_name: str = "resources"):
        match cwd:
            case None:
                self.cwd = Path(__file__).parent.parent
                self.resources_path = self.get_resources(name=resources_name)
            case Path():
                if cwd.is_dir():
                    self.cwd = cwd
                else:
                    self.cwd = Path("")
                self.resources_path = self.cwd

    def get_resources(self, name: str = "resources") -> Path:
        path = self.cwd / name
        if not path.is_dir():
            raise NotADirectoryError(f"{path=}")
        return path

    def get_image_files(
        self, file_ext: str = ".png", exclude_kw: str = ""
    ) -> list[Path]:
        if exclude_kw:
            imgs = [
                fp
                for fp in self.resources_path.rglob(f"*{file_ext}")
                if exclude_kw not in fp.stem
            ]
        else:
            imgs = [fp for fp in self.resources_path.rglob(f"*{file_ext}")]

        if not imgs:
            raise FileNotFoundError(f"no files found {file_ext=}")
        return imgs

    def generate_output_dir(self, name: str = "output"):
        output_dir = self.resources_path / name
        if not output_dir.is_dir():
            output_dir.mkdir()
        return output_dir

    def get_filetable(self) -> pd.DataFrame:
        df = pd.DataFrame(pd.Series(self.get_image_files()), columns=["filepath"])
        df["foldername"] = df["filepath"].apply(lambda x: x.parent.name)
        return df


def main():
    fm = PathFinder()
    # imgs = fm.get_image_files(".png")
    # [print(x) for x in imgs]
    df = fm.get_filetable()


if __name__ == "__main__":
    main()
