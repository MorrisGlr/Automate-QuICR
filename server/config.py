from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    output_dir: str = "generated_output"
    data_dir: str = "data"
    default_model: str = "o4-mini-2025-04-16"
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def output_path(self) -> Path:
        return self.project_root / self.output_dir

    @property
    def data_path(self) -> Path:
        return self.project_root / self.data_dir

    @property
    def guidelines_path(self) -> Path:
        return self.data_path / "guidelines" / "guidelines.json"


settings = Settings()
