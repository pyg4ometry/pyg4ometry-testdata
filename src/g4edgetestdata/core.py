from __future__ import annotations

import logging
import os
from getpass import getuser
from pathlib import Path, PurePath
from tempfile import gettempdir

from git import GitCommandError, InvalidGitRepositoryError, Repo

log = logging.getLogger(__name__)


class G4EdgeTestData:
    """
    Class to access all test data. Data can be accessed via the path using the
    [] operator. A full list of available files (built dynamically) is given in
    the member `files`.

    >>> d = G4EdgeTestData()
    >>> d.files
        ['convert/T001_geant4Box2Fluka.gdml',
         'convert/T001_geant4Box2Fluka.inp',
         'convert/T001_geant4Box2Fluka_baked.inp',
        ...
    >>> abs_path = d['convert/T001_geant4Box2Fluka.inp']
    """

    def __init__(self):
        self._default_git_ref = "main"
        self._repo_path = Path(
            os.getenv("G4EDGE_TESTDATA", gettempdir() + "/g4edge-testdata-" + getuser())
        )
        self._repo: Repo = self._init_testdata_repo()
        self._build_list_of_available_data()

    def _init_testdata_repo(self) -> None:
        if not self._repo_path.is_dir():
            self._repo_path.mkdir()

        repo = None
        try:
            repo = Repo(self._repo_path)
        except InvalidGitRepositoryError:
            log.info(
                "Cloning https://github.com/g4edge/testdata in %s...",
                str(self._repo_path),
            )
            repo = Repo.clone_from(
                "https://github.com/g4edge/testdata", self._repo_path
            )

        repo.git.checkout(self._default_git_ref)

        return repo

    def checkout(self, git_ref: str) -> None:
        try:
            self._repo.git.checkout(git_ref)
        except GitCommandError:
            self._repo.remote().pull()
            self._repo.git.checkout(git_ref)

    def reset(self) -> None:
        self._repo.git.checkout(self._default_git_ref)

    def __getitem__(self, filename: str | Path) -> Path:
        """Get an absolute path to a G4Edge test data file.

        Parameters
        ----------
        filename : str
            path of the file relative to g4edge/testdata/data
        """
        full_path = (self._repo_path / "data" / filename).resolve()

        if not full_path.exists():
            msg = f'Test file/directory "{filename}" not found in g4edge/testdata repository'
            raise FileNotFoundError(msg)

        return full_path

    def _build_list_of_available_data(self):
        """
        Build a list of all available data dynamically. From python 3.12 we could use
        `Path.walk`, but we use down to 3.7, therefore use the `os.walk` method instead.
        """
        self.files = []
        root = Path(self._repo_path / "data")
        for dirpath, _dirnames, filenames in os.walk(root):
            for f in filenames:
                common = os.path.relpath(dirpath, root)
                rp = PurePath(common) / f
                self.files.append(str(rp))
        self.files = sorted(self.files)
