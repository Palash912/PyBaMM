import os
import sys
import subprocess
<<<<<<< HEAD
from pathlib import Path
=======
import tarfile
import glob
import pathlib
from shutil import copy
from platform import python_version
>>>>>>> parent of 65a670cd... Remove package_data dict from setup.py

import wheel.bdist_wheel as orig

try:
    from setuptools import setup, find_packages, Extension
    from setuptools.command.build_ext import build_ext
except ImportError:
    from distutils.core import setup, find_packages
    from distutils.command.build_ext import build_ext


class bdist_wheel(orig.bdist_wheel):
    """A custom install command to add 2 build options"""

    user_options = orig.bdist_wheel.user_options + [
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        orig.bdist_wheel.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        orig.bdist_wheel.finalize_options(self)

    def run(self):
        orig.bdist_wheel.run(self)


class CMakeBuild(build_ext):
    user_options = build_ext.user_options + [
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        build_ext.finalize_options(self)
        self.set_undefined_options(
            "bdist_wheel",
            ("suitesparse_root", "suitesparse_root"),
            ("sundials_root", "sundials_root"),
        )

    def run(self):
        try:
            subprocess.run(["cmake", "--version"])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the KLU python module."
            )

        try:
            assert os.path.isfile("third-party/pybind11/tools/pybind11Tools.cmake")
        except AssertionError:
            print(
                "Error: Could not find "
                "third-party/pybind11/pybind11/tools/pybind11Tools.cmake"
            )
            print("Make sure the pybind11 repository was cloned in ./third-party/")
            print("See installation instructions for more information.")

        cmake_args = ["-DPYTHON_EXECUTABLE={}".format(sys.executable)]
        if self.suitesparse_root:
            cmake_args.append(
                "-DSuiteSparse_ROOT={}".format(os.path.abspath(self.suitesparse_root))
            )
        if self.sundials_root:
            cmake_args.append(
                "-DSUNDIALS_ROOT={}".format(os.path.abspath(self.sundials_root))
            )

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        cmake_list_dir = os.path.abspath(os.path.dirname(__file__))
        print("-" * 10, "Running CMake for idaklu solver", "-" * 40)
        subprocess.run(["cmake", cmake_list_dir] + cmake_args, cwd=self.build_temp)

        print("-" * 10, "Building idaklu module", "-" * 40)
        subprocess.run(["cmake", "--build", "."], cwd=self.build_temp)

        # Move from build temp to final position
        for ext in self.extensions:
            self.move_output(ext)

    def move_output(self, ext):
        build_temp = Path(self.build_temp).resolve()
        dest_path = Path(self.get_ext_fullpath(ext.name)).resolve()
        source_path = build_temp / self.get_ext_filename(ext.name)
        dest_directory = dest_path.parents[0]
        dest_directory.mkdir(parents=True, exist_ok=True)
        self.copy_file(source_path, dest_path)


# Build the list of package data files to be included in the PyBaMM package.
# These are mainly the parameter files located in the input/parameters/ subdirectories.
pybamm_data = []
for file_ext in ["*.csv", "*.py", "*.md"]:
    # Get all the files ending in file_ext in pybamm/input dir.
    # list_of_files = [
    #    'pybamm/input/drive_cycles/car_current.csv',
    #    'pybamm/input/drive_cycles/US06.csv',
    # ...
    list_of_files = glob.glob("pybamm/input/**/" + file_ext, recursive=True)

    # Add these files to pybamm_data.
    # The path must be relative to the package dir (pybamm/), so
    # must process the content of list_of_files to take out the top
    # pybamm/ dir, i.e.:
    # ['input/drive_cycles/car_current.csv',
    #  'input/drive_cycles/US06.csv',
    # ...
    pybamm_data.extend(
        [os.path.join(*pathlib.Path(filename).parts[1:]) for filename in list_of_files]
    )
pybamm_data.append("./version")
pybamm_data.append("./CITATIONS.txt")

setup(
    name="pybamm",
    version="1.0",
    description="Python Battery Mathematical Modelling.",
    long_description="description",
    long_description_content_type="text/markdown",
    url="https://github.com/pybamm-team/PyBaMM",
    # include_package_data=True,
    packages=find_packages(include=("pybamm", "pybamm.*")),
    ext_modules=[Extension("idaklu", ["pybamm/solvers/c_solvers/idaklu.cpp"])],
    cmdclass={"build_ext": CMakeBuild, "bdist_wheel": bdist_wheel},
    package_data={"pybamm": pybamm_data},
    # List of dependencies
    install_requires=[
        "numpy>=1.16",
        "scipy>=1.3",
        "pandas>=0.24",
        "anytree>=2.4.3",
        "autograd>=1.2",
        "scikit-fem>=0.2.0",
        "casadi>=3.5.0",
        "jupyter",  # For example notebooks
        # Note: Matplotlib is loaded for debug plots, but to ensure pybamm runs
        # on systems without an attached display, it should never be imported
        # outside of plot() methods.
        # Should not be imported
        "matplotlib>=2.0",
    ],
    extras_require={
        "docs": ["sphinx>=1.5", "guzzle-sphinx-theme"],  # For doc generation
        "dev": [
            "flake8>=3",  # For code style checking
            "black",  # For code style auto-formatting
        ],
    },
    entry_points={
        "console_scripts": [
            "pybamm_edit_parameter = pybamm.parameters_cli:edit_parameter",
            "pybamm_add_parameter = pybamm.parameters_cli:add_parameter",
            "pybamm_list_parameters = pybamm.parameters_cli:list_parameters",
        ],
    },
)
