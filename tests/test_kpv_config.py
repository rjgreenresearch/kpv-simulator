if not self.data_root.exists():
    raise RuntimeError(f"KPV data directory does not exist: {self.data_root}")
