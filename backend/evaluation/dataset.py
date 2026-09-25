import json
from pathlib import Path


class EvaluationDataset:

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self):
        """
        Load evaluation questions.
        """

        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)