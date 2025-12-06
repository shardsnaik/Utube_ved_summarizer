import yaml
from pathlib import Path

def read_yaml(path: Path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)
    

class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                value = DictToObject(value)
            setattr(self, key, value)


class AppConfig:

    def __init__(self, config_path = 'params.yaml'):
        self.readed_yaml = read_yaml(Path(config_path))
        self.config = DictToObject(self.readed_yaml)

        # self._build_paths()
        
                


    # def _build_paths(self):
    #     model_dir = Path(self.config.paths.model_dir)
    #     # summary_model = self.config.models.summarizer_model

    #     # # Create computed paths
    #     # self.config.models.full_model_path = model_dir / summary_model

    #     audio_dir = Path(self.config.paths.audio_dir)
    #     output_dir = Path(self.config.paths.output_dir)

    #     # Ensure directories exist
    #     output_dir.mkdir(parents=True, exist_ok=True)
    #     audio_dir.mkdir(parents=True, exist_ok=True)
