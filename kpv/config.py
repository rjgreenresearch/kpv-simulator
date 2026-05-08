from pathlib import Path
import yaml

def load_config():
    config_path = Path(__file__).resolve().parent / "kpv_config.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Always resolve to an absolute path
    cfg["data_root"] = str(Path(cfg["data_root"]).resolve())
    return cfg
