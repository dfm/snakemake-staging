from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

from snakemake_staging.utils import PathLike, path_to_identifier, working_directory

STAGES: OrderedDict[str, "Stage"] = OrderedDict()


def get_stages_to_restore(config: Dict[str, Any]) -> List[str]:
    restore = config.get("restore", [])
    if isinstance(restore, (str, Path)):
        restore = [restore]
    return restore


class Stage(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.files: OrderedDict[str, PathLike] = OrderedDict()
        self.to_restore = self.name in get_stages_to_restore(self.config)
        self.directory = working_directory(
            "staging", "stages", self.name, config=self.config
        )
        STAGES[name] = self

    def __call__(self, *files: PathLike) -> List[PathLike]:
        return self.staged(*files)

    def staged(self, *files: PathLike) -> List[PathLike]:
        # Extract the list of stages we want to restore from the config
        restore = get_stages_to_restore(self.config)

        # Add this list of files to the database of files for this stage
        for file in files:
            if file in self.files:
                raise RuntimeError(
                    f"Duplicate file detected in stage {self.name}: {file}"
                )
            self.files[path_to_identifier(file)] = file

        # If we're restoring this stage, we short-circuit this rule so that it won't
        # ever be run to generate the staged files
        if self.name in restore:
            return []
        else:
            return list(files)

    @abstractmethod
    def snapshot(self) -> None:
        ...

    @abstractmethod
    def restore(self) -> None:
        ...


class NoOpStage(Stage):
    def snapshot(self) -> None:
        pass

    def restore(self) -> None:
        pass
