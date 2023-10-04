import os
import shutil
from main import update_config_details
import config
import commons as cf
from makeppt import PptManager
from utils import PathFinder

cfg = config.Config(config_filename="config.yml", hard_reset=False)
cfg = update_config_details(cfg)
log = cfg.log


def test_detect_images():
    fmgr = PathFinder(cwd=cfg.user_folders["inpf01"])
    try:
        imgs = fmgr.get_image_files()
    except Exception:
        # band aid to show example, this code will not be used
        imgs = []

    if len(imgs) > 0:
        return
    else:
        log.error("No images found, extracting examples from resource folder...")
        resource_mgr = PathFinder()
        imgs = resource_mgr.get_image_files()
        for img in imgs:
            shutil.copy(img, cfg.user_folders["inpf01"])
            log.info(f"copied {img.name}")

        imgs = fmgr.get_image_files()
        assert len(imgs) > 0


def test_main_production_run():
    ppt = PptManager(cfg, cfg.user_files["ppt_template1"])
    fm = PathFinder(cwd=cfg.user_folders["inpf01"])
    imgs = fm.get_image_files(".png")
    ppt.insert_images_wafersPerLot("images", imgs)
    ppt.save_ppt(outname=f"pytest-results-{cf.get_time()}.pptx")
    for img in imgs:
        log.error(f"removing {img.name}")
        os.remove(img)
