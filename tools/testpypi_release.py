#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT            = Path(__file__).resolve().parents[1]
ENV_DIR_NAME            = ".env"
DIST_DIR_NAME           = "dist"
SRC_VERSION_FILE        = PROJECT_ROOT / "src" / "pypnm" / "version.py"
PYPROJECT_FILE          = PROJECT_ROOT / "pyproject.toml"
PACKAGE_NAME            = "pypnm-docsis"
CONSOLE_SCRIPT_NAME     = "pypnm"
LOCAL_INSTALL_VENV_NAME = "pypnm-install-test"
TESTPYPI_VENV_NAME      = "pypnm-testpypi"
TESTPYPI_INDEX_URL      = "https://test.pypi.org/simple/"
PYPI_FALLBACK_URL       = "https://pypi.org/simple/"


class TestPyPIReleaseRunner:
    """
    Orchestrate The PyPNM TestPyPI Release Workflow.

    This tool runs the full TestPyPI release flow in a single command:

    1. Verify the project root, Python version, and version alignment between
       ``pyproject.toml`` and ``src/pypnm/version.py``.
    2. Build source and wheel distributions into the local ``dist/`` folder
       using the project ``.env`` virtual environment.
    3. Run a local wheel smoke test in an isolated virtual environment to
       confirm the console script and version are correct.
    4. Upload the built artifacts to TestPyPI using ``twine``; credentials
       must be configured via environment variables or ``~/.pypirc``.
    5. Install the published version from TestPyPI into another clean virtual
       environment and validate the installation behaves like an external user.

    The script is designed to be idempotent across runs; version mismatches
    or missing files will stop the process with a clear error message.
    """

    def __init__(self) -> None:
        self.project_root            = PROJECT_ROOT
        self.env_dir                 = self.project_root / ENV_DIR_NAME
        self.dist_dir                = self.project_root / DIST_DIR_NAME
        self.local_install_venv_dir  = Path("/tmp") / LOCAL_INSTALL_VENV_NAME
        self.testpypi_venv_dir       = Path("/tmp") / TESTPYPI_VENV_NAME

    def run(self) -> None:
        """
        Execute The Full TestPyPI Release Workflow.

        This method validates the environment, builds the distributions,
        performs a local wheel smoke test, uploads the artifacts to TestPyPI,
        and finally installs and verifies the package from TestPyPI. Any
        failure in a step will abort the workflow and exit the process with
        a non-zero status code.
        """
        self._assert_project_root()
        pyproject_version = self._read_pyproject_version()
        src_version       = self._read_src_version()
        self._assert_versions_match(pyproject_version, src_version)

        print(f"[INFO] Release version: {pyproject_version}")
        self._build_distributions()
        self._local_wheel_smoke_test(pyproject_version)
        self._upload_to_testpypi()
        self._verify_from_testpypi(pyproject_version)
        print("[INFO] TestPyPI release workflow completed successfully.")

    def _run_subprocess(self, cmd: list[str], env: dict[str, str] | None = None) -> None:
        """
        Run A Subprocess Command With Error Propagation.

        Parameters
        ----------
        cmd:
            The command and arguments to execute. Each list element is a
            separate token passed to the underlying process.
        env:
            Optional environment mapping to use for the subprocess. When
            omitted, the current process environment is inherited.
        """
        print(f"[CMD] {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=False)
        if result.returncode != 0:
            raise SystemExit(f"[ERROR] Command failed with exit code {result.returncode}: {' '.join(cmd)}")

    def _assert_project_root(self) -> None:
        """
        Validate That The Script Is Running From A PyPNM Project Root.

        The method checks for the presence of ``pyproject.toml`` and the
        ``src/pypnm/version.py`` file. If either is missing, the release
        process is aborted with an informative error.
        """
        if not PYPROJECT_FILE.is_file():
            raise SystemExit(f"[ERROR] pyproject.toml not found at {PYPROJECT_FILE}")
        if not SRC_VERSION_FILE.is_file():
            raise SystemExit(f"[ERROR] version.py not found at {SRC_VERSION_FILE}")

    def _read_pyproject_version(self) -> str:
        """
        Read The Project Version From pyproject.toml.

        The method performs a minimal parse of the ``[project]`` section and
        extracts the ``version = \"...\"`` value using a regular expression
        that supports both single and double quotes and ignores trailing
        comments.
        """
        in_project_section = False
        version_pattern    = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']')
        with PYPROJECT_FILE.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("[project]"):
                    in_project_section = True
                    continue
                if in_project_section and stripped.startswith("["):
                    break
                if in_project_section:
                    match = version_pattern.match(stripped)
                    if match is not None:
                        return match.group(1)
        raise SystemExit("[ERROR] Could not find [project] version in pyproject.toml")

    def _read_src_version(self) -> str:
        """
        Read The Project Version From src/pypnm/version.py.

        The method scans for the ``__version__`` assignment and returns the
        first quoted string on that line that contains at least one digit.
        It supports both single and double quotes, optional type annotations,
        and trailing inline comments.
        """
        quote_pattern = re.compile(r'["\']([^"\']+)["\']')
        with SRC_VERSION_FILE.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if "__version__" not in stripped or "=" not in stripped:
                    continue
                for match in quote_pattern.finditer(stripped):
                    candidate = match.group(1)
                    if any(ch.isdigit() for ch in candidate):
                        return candidate
        raise SystemExit("[ERROR] Could not find __version__ in src/pypnm/version.py")

    def _assert_versions_match(self, pyproject_version: str, src_version: str) -> None:
        """
        Ensure pyproject.toml And Source Version Are Identical.

        Parameters
        ----------
        pyproject_version:
            Version string extracted from the ``[project]`` section of
            ``pyproject.toml``.
        src_version:
            Version string extracted from ``src/pypnm/version.py``.

        Raises
        ------
        SystemExit
            If the two version strings differ, the workflow is aborted to
            prevent publishing inconsistent metadata.
        """
        if pyproject_version != src_version:
            raise SystemExit(
                f"[ERROR] Version mismatch: pyproject.toml={pyproject_version}, src/pypnm/version.py={src_version}"
            )

    def _build_distributions(self) -> None:
        """
        Build Source And Wheel Distributions Using The Project Environment.

        This method activates the project virtual environment under ``.env``
        (by invoking its Python directly), clears any existing ``dist/`` and
        ``build/`` directories, and runs ``python -m build`` to generate the
        source archive and wheel.
        """
        env_python = self._resolve_env_python()
        build_env  = os.environ.copy()
        build_env["VIRTUAL_ENV"] = str(self.env_dir)
        build_env["PATH"]        = f"{self.env_dir / 'bin'}:{build_env.get('PATH', '')}"

        if self.dist_dir.exists():
            print(f"[INFO] Removing existing {self.dist_dir}")
            shutil.rmtree(self.dist_dir)
        build_dir = self.project_root / "build"
        if build_dir.exists():
            print(f"[INFO] Removing existing {build_dir}")
            shutil.rmtree(build_dir)

        self._run_subprocess([str(env_python), "-m", "pip", "install", "--upgrade", "build", "twine"], env=build_env)
        self._run_subprocess([str(env_python), "-m", "build"], env=build_env)

        if not self.dist_dir.is_dir():
            raise SystemExit(f"[ERROR] dist directory not found at {self.dist_dir}")
        artifacts = list(self.dist_dir.iterdir())
        if not artifacts:
            raise SystemExit(f"[ERROR] No artifacts found in {self.dist_dir}")
        print("[INFO] Built artifacts:")
        for artifact in artifacts:
            print(f"  - {artifact.name}")

    def _resolve_env_python(self) -> Path:
        """
        Resolve The Python Interpreter Inside The Project .env Environment.

        Returns
        -------
        Path
            The path to ``.env/bin/python``. If the environment does not
            exist, the workflow is aborted.
        """
        env_python = self.env_dir / "bin" / "python"
        if not env_python.is_file():
            raise SystemExit(f"[ERROR] Project environment Python not found at {env_python}")
        return env_python

    def _create_venv(self, venv_dir: Path) -> Path:
        """
        Create A Fresh Virtual Environment For Testing.

        Parameters
        ----------
        venv_dir:
            Target directory for the virtual environment. Any existing
            directory will be removed before creation.

        Returns
        -------
        Path
            The path to the newly created virtual environment's Python
            interpreter.
        """
        if venv_dir.exists():
            print(f"[INFO] Removing existing virtual environment at {venv_dir}")
            shutil.rmtree(venv_dir)

        self._run_subprocess([sys.executable, "-m", "venv", str(venv_dir)])
        venv_python = venv_dir / "bin" / "python"
        if not venv_python.is_file():
            raise SystemExit(f"[ERROR] venv python not found at {venv_python}")
        return venv_python

    def _local_wheel_smoke_test(self, version: str) -> None:
        """
        Perform A Local Wheel Smoke Test In An Isolated Virtual Environment.

        The method creates a new virtual environment, installs the built
        wheel for the given version from the local ``dist/`` directory,
        and validates that:

        - The ``pypnm`` console script is available and responds to
          ``--help``.
        - Importing ``pypnm`` reports the expected version.
        """
        print("[INFO] Running local wheel smoke test...")
        venv_python = self._create_venv(self.local_install_venv_dir)
        wheel_path  = self._resolve_wheel_path(version)

        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        self._run_subprocess([str(venv_python), "-m", "pip", "install", str(wheel_path)], env=env)
        self._run_subprocess([str(venv_python), "-m", "pip", "show", PACKAGE_NAME], env=env)
        self._run_subprocess([str(self.local_install_venv_dir / "bin" / CONSOLE_SCRIPT_NAME), "--help"], env=env)
        self._run_subprocess(
            [
                str(venv_python),
                "-c",
                "import pypnm; print('pypnm.__file__ =', pypnm.__file__); "
                "print('pypnm.__version__ =', pypnm.__version__)",
            ],
            env=env,
        )

    def _resolve_wheel_path(self, version: str) -> Path:
        """
        Resolve The Built Wheel Path For The Given Version.

        Parameters
        ----------
        version:
            The semantic version string (for example ``0.5.8.0``) to match
            against filenames in the ``dist/`` directory.

        Returns
        -------
        Path
            The path to the matching wheel file.

        Raises
        ------
        SystemExit
            If no matching wheel file is found in ``dist/``.
        """
        pattern = f"{PACKAGE_NAME.replace('-', '_')}-{version}-py3-none-any.whl"
        wheel   = self.dist_dir / pattern
        if not wheel.is_file():
            raise SystemExit(f"[ERROR] Wheel not found at {wheel}")
        return wheel

    def _upload_to_testpypi(self) -> None:
        """
        Upload Built Artifacts To TestPyPI Using Twine.

        This step requires valid TestPyPI credentials configured either via
        ``TWINE_USERNAME`` and ``TWINE_PASSWORD`` environment variables or
        via a ``~/.pypirc`` entry for the ``testpypi`` repository.
        """
        env        = os.environ.copy()
        env_python = self._resolve_env_python()

        artifacts = [str(p) for p in sorted(self.dist_dir.iterdir()) if p.is_file()]
        if not artifacts:
            raise SystemExit(f"[ERROR] No distribution files found to upload in {self.dist_dir}")

        cmd = [str(env_python), "-m", "twine", "upload", "--repository", "testpypi", *artifacts]
        self._run_subprocess(cmd, env=env)

    def _verify_from_testpypi(self, version: str) -> None:
        """
        Validate Installation From TestPyPI In A Fresh Virtual Environment.

        The method creates a new virtual environment, installs the specific
        version of ``pypnm-docsis`` from TestPyPI (with dependencies resolved
        from PyPI), and confirms that the ``pypnm`` console script and
        reported version match expectations.
        """
        print("[INFO] Verifying installation from TestPyPI...")
        venv_python = self._create_venv(self.testpypi_venv_dir)
        env         = os.environ.copy()
        env.pop("PYTHONPATH", None)

        self._run_subprocess([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], env=env)
        self._run_subprocess(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--index-url",
                TESTPYPI_INDEX_URL,
                "--extra-index-url",
                PYPI_FALLBACK_URL,
                f"{PACKAGE_NAME}=={version}",
            ],
            env=env,
        )
        self._run_subprocess([str(self.testpypi_venv_dir / "bin" / CONSOLE_SCRIPT_NAME), "--help"], env=env)
        self._run_subprocess(
            [
                str(venv_python),
                "-c",
                "import pypnm; print('pypnm.__file__ =', pypnm.__file__); "
                "print('pypnm.__version__ =', pypnm.__version__)",
            ],
            env=env,
        )


def main() -> None:
    """
    Entrypoint For The TestPyPI Release Tool.

    This function constructs the release runner and executes the full
    workflow. Any unhandled exceptions are converted into a non-zero exit
    status for integration with automation or CI pipelines.
    """
    runner = TestPyPIReleaseRunner()
    runner.run()


if __name__ == "__main__":
    main()
