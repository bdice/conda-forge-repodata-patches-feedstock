# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import defaultdict
from contextlib import suppress
import copy
import json
import os
from os.path import join, isdir
import sys
import tqdm
import re
import requests
import packaging.version
from packaging.version import parse as parse_version
from concurrent.futures import ProcessPoolExecutor

from get_license_family import get_license_family
from patch_yaml_utils import (
    patch_yaml_edit_index,
    _extract_track_feature,
    _replace_pin,
    _rename_dependency,
    _relax_exact,
    _pin_stricter,
    _pin_looser,
    CB_PIN_REGEX,
    pad_list,
)

CHANNEL_NAME = "conda-forge"
CHANNEL_ALIAS = "https://conda.anaconda.org"
SUBDIRS = (
    "noarch",
    "linux-64",
    "linux-armv7l",
    "linux-aarch64",
    "linux-ppc64le",
    "osx-64",
    "osx-arm64",
    "win-32",
    "win-64",
)

REMOVALS = {
    "noarch": (
        "sendgrid-5.3.0-py_0.tar.bz2",
    ),
    "linux-64": (
        "airflow-with-gcp_api-1.9.0-1.tar.bz2",
        "airflow-with-gcp_api-1.9.0-2.tar.bz2",
        "airflow-with-gcp_api-1.9.0-3.tar.bz2",
        "adios-1.13.1-py36hbecc8f4_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "gdk-pixbuf-2.36.9-0.tar.bz2",
        "itk-4.12.0-py27_0.tar.bz2",
        "itk-4.12.0-py35_0.tar.bz2",
        "itk-4.12.0-py36_0.tar.bz2",
        "itk-4.13.0-py27_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "itk-4.13.0-py36_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_1.tar.bz2",
        "libtasn1-4.13-py36_0.tar.bz2",
        "libgsasl-1.8.0-py36_1.tar.bz2",
        "nipype-0.12.0-0.tar.bz2",
        "nipype-0.12.0-py35_0.tar.bz2",
        "postgis-2.4.3+9.6.8-0.tar.bz2",
        "pyarrow-0.1.post-0.tar.bz2",
        "pyarrow-0.1.post-1.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
        "rapidpy-2.5.2-py36_0.tar.bz2",
        "smesh-8.3.0b0-1.tar.bz2",
        "statuspage-0.3.3-0.tar.bz2",
        "statuspage-0.4.0-0.tar.bz2",
        "statuspage-0.4.1-0.tar.bz2",
        "statuspage-0.5.0-0.tar.bz2",
        "statuspage-0.5.1-0.tar.bz2",
        "tokenize-rt-2.0.1-py27_0.tar.bz2",
        "vaex-core-0.4.0-py27_0.tar.bz2",
    ),
    "osx-64": (
        "adios-1.13.1-py36hbecc8f4_0.tar.bz2",
        "airflow-with-gcp_api-1.9.0-1.tar.bz2",
        "airflow-with-gcp_api-1.9.0-2.tar.bz2",
        "arpack-3.6.1-blas_openblash1f444ea_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np110py27_1.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_0.tar.bz2",
        "ecmwf_grib-1.14.7-np111py27_1.tar.bz2",
        "flask-rest-orm-0.5.0-py35_0.tar.bz2",
        "flask-rest-orm-0.5.0-py36_0.tar.bz2",
        "itk-4.12.0-py27_0.tar.bz2",
        "itk-4.12.0-py35_0.tar.bz2",
        "itk-4.12.0-py36_0.tar.bz2",
        "itk-4.13.0-py27_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "itk-4.13.0-py36_0.tar.bz2",
        "lammps-2018.03.16-.tar.bz2",
        "libtasn1-4.13-py36_0.tar.bz2",
        "mpb-1.6.2-1.tar.bz2",
        "nipype-0.12.0-0.tar.bz2",
        "nipype-0.12.0-py35_0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
        "reentry-1.1.0-py27_0.tar.bz2",
        "resampy-0.2.0-py27_0.tar.bz2",
        "statuspage-0.3.3-0.tar.bz2",
        "statuspage-0.4.0-0.tar.bz2",
        "statuspage-0.4.1-0.tar.bz2",
        "statuspage-0.5.0-0.tar.bz2",
        "statuspage-0.5.1-0.tar.bz2",
        "sundials-3.1.0-blas_openblash0edd121_202.tar.bz2",
        "vlfeat-0.9.20-h470a237_2.tar.bz2",
        "xtensor-python-0.19.1-h3e44d54_0.tar.bz2",
    ),
    "osx-arm64": (
    ),
    "win-32": (
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "glpk-4.59-py27_vc9_0.tar.bz2",
        "glpk-4.59-py34_vc10_0.tar.bz2",
        "glpk-4.59-py35_vc14_0.tar.bz2",
        "glpk-4.60-py27_vc9_0.tar.bz2",
        "glpk-4.60-py34_vc10_0.tar.bz2",
        "glpk-4.60-py35_vc14_0.tar.bz2",
        "glpk-4.61-py27_vc9_0.tar.bz2",
        "glpk-4.61-py35_vc14_0.tar.bz2",
        "glpk-4.61-py36_0.tar.bz2",
        "libspatialindex-1.8.5-py27_0.tar.bz2",
        "liknorm-1.3.7-py27_1.tar.bz2",
        "liknorm-1.3.7-py35_1.tar.bz2",
        "liknorm-1.3.7-py36_1.tar.bz2",
        "nlopt-2.4.2-0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",

    ),
    "win-64": (
        "compliance-checker-2.2.0-0.tar.bz2",
        "compliance-checker-3.0.3-py27_0.tar.bz2",
        "compliance-checker-3.0.3-py35_0.tar.bz2",
        "compliance-checker-3.0.3-py36_0.tar.bz2",
        "cookiecutter-1.4.0-0.tar.bz2",
        "doconce-1.0.0-py27_0.tar.bz2",
        "doconce-1.0.0-py27_1.tar.bz2",
        "doconce-1.0.0-py27_2.tar.bz2",
        "doconce-1.0.0-py27_3.tar.bz2",
        "doconce-1.0.0-py27_4.tar.bz2",
        "doconce-1.4.0-py27_0.tar.bz2",
        "doconce-1.4.0-py27_1.tar.bz2",
        "glpk-4.59-py27_vc9_0.tar.bz2",
        "glpk-4.59-py34_vc10_0.tar.bz2",
        "glpk-4.59-py35_vc14_0.tar.bz2",
        "glpk-4.60-py27_vc9_0.tar.bz2",
        "glpk-4.60-py34_vc10_0.tar.bz2",
        "glpk-4.60-py35_vc14_0.tar.bz2",
        "glpk-4.61-py27_vc9_0.tar.bz2",
        "glpk-4.61-py35_vc14_0.tar.bz2",
        "glpk-4.61-py36_0.tar.bz2",
        "itk-4.13.0-py35_0.tar.bz2",
        "libspatialindex-1.8.5-py27_0.tar.bz2",
        "liknorm-1.3.7-py27_1.tar.bz2",
        "liknorm-1.3.7-py35_1.tar.bz2",
        "liknorm-1.3.7-py36_1.tar.bz2",
        "nlopt-2.4.2-0.tar.bz2",
        "pygpu-0.6.5-0.tar.bz2",
        "pytest-regressions-1.0.1-0.tar.bz2",
    ),
}

OSX_SDK_FIXES = {
    'nodejs-12.8.0-hec2bf70_1': '10.10',
    'nodejs-12.1.0-h6de7cb9_1': '10.10',
    'nodejs-12.3.1-h6de7cb9_0': '10.10',
    'nodejs-12.9.0-hec2bf70_0': '10.10',
    'nodejs-12.9.1-hec2bf70_0': '10.10',
    'nodejs-12.7.0-hec2bf70_1': '10.10',
    'nodejs-12.10.0-hec2bf70_0': '10.10',
    'nodejs-12.4.0-h6de7cb9_0': '10.10',
    'nodejs-12.11.1-hec2bf70_0': '10.10',
    'nodejs-12.7.0-h6de7cb9_0': '10.10',
    'nodejs-12.3.0-h6de7cb9_0': '10.10',
    'nodejs-10.16.3-hec2bf70_0': '10.10',
    'nodejs-12.12.0-hfddbe92_0': '10.10',
    'nodejs-12.8.1-hec2bf70_0': '10.10',
    'javafx-sdk-11.0.4-h6dcaf97_1': '10.11',
    'javafx-sdk-12.0.2-h6dcaf97_1': '10.11',
    'javafx-sdk-12.0.2-h6dcaf97_0': '10.11',
    'javafx-sdk-11.0.4-h6dcaf97_0': '10.11',
    'qt-5.12.1-h1b46049_0': '10.12',
    'qt-5.9.7-h8cf7e54_3': '10.12',
    'qt-5.9.7-h93ee506_0': '10.12',
    'qt-5.9.7-h93ee506_1': '10.12',
    'qt-5.12.5-h1b46049_0': '10.12',
    'qt-5.9.7-h93ee506_2': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_2': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_1': '10.12',
    'openmpi-mpicxx-4.0.1-h6052eea_0': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_2': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_0': '10.12',
    'openmpi-mpicxx-4.0.1-hc9558a2_1': '10.12',
    'freecad-0.18.3-py37h4764a83_2': '10.12',
    'freecad-0.18.3-py37hc453731_1': '10.12',
    'freecad-0.18.4-py37hab2b3aa_1': '10.12',
    'freecad-0.18.4-py37hab2b3aa_0': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_1': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_2': '10.12',
    'openmpi-mpicc-4.0.1-h24e1f75_0': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_0': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_1': '10.12',
    'openmpi-mpicc-4.0.1-h516909a_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_0': '10.12',
    'openmpi-mpifort-4.0.1-h6ad152f_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_2': '10.12',
    'openmpi-mpifort-4.0.1-h939af09_1': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_0': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_1': '10.12',
    'openmpi-mpifort-4.0.1-he991be0_2': '10.12',
    'reaktoro-1.0.7-py37h99eb986_0': '10.12',
    'reaktoro-1.0.7-py37h99eb986_1': '10.12',
    'reaktoro-1.0.7-py36h99eb986_0': '10.12',
    'reaktoro-1.0.7-py36h99eb986_1': '10.12',
    'pyqt-5.12.3-py38he22c54c_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_0': '10.12',
    'pyqt-5.12.3-py36he22c54c_1': '10.12',
    'pyqt-5.9.2-py27h2a560b1_4': '10.12',
    'pyqt-5.9.2-py27h2a560b1_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_4': '10.12',
    'pyqt-5.9.2-py36h2a560b1_3': '10.12',
    'pyqt-5.9.2-py27h2a560b1_2': '10.12',
    'pyqt-5.9.2-py36h2a560b1_1': '10.12',
    'pyqt-5.12.3-py27h2a560b1_0': '10.12',
    'pyqt-5.12.3-py37h2a560b1_0': '10.12',
    'pyqt-5.12.3-py27he22c54c_0': '10.12',
    'pyqt-5.12.3-py27he22c54c_1': '10.12',
    'pyqt-5.9.2-py37h2a560b1_2': '10.12',
    'pyqt-5.9.2-py37h2a560b1_1': '10.12',
    'pyqt-5.9.2-py36h2a560b1_0': '10.12',
    'pyqt-5.9.2-py36h2a560b1_4': '10.12',
    'pyqt-5.9.2-py27h2a560b1_0': '10.12',
    'pyqt-5.9.2-py37h2a560b1_3': '10.12',
    'pyqt-5.12.3-py38he22c54c_0': '10.12',
    'pyqt-5.9.2-py27h2a560b1_3': '10.12',
    'pyqt-5.9.2-py36h2a560b1_2': '10.12',
    'pyqt-5.12.3-py37he22c54c_0': '10.12',
    'pyqt-5.12.3-py36he22c54c_0': '10.12',
    'pyqt-5.12.3-py37he22c54c_1': '10.12',
    'pyqt-5.12.3-py36h2a560b1_0': '10.12',
    'ldas-tools-al-2.6.3-hf543496_0': '10.12',
    'ldas-tools-al-2.6.3-hf543496_1': '10.12',
    'ldas-tools-al-2.6.4-h4f290e7_1': '10.12',
    'ldas-tools-al-2.6.4-h4f290e7_0': '10.12',
    'openmpi-4.0.1-ha90c164_2': '10.12',
    'openmpi-4.0.1-ha90c164_0': '10.12',
    'openmpi-4.0.1-hfcebdee_2': '10.12',
    'openmpi-4.0.1-ha90c164_1': '10.12',
    'openmpi-4.0.1-hc99cbb1_1': '10.12',
    'openmpi-4.0.1-hc99cbb1_0': '10.12',
    'openmpi-4.0.1-hc99cbb1_2': '10.12',
}


def _add_removals(instructions, subdir):
    r = requests.get(
        "https://conda.anaconda.org/conda-forge/"
        "label/broken/%s/repodata.json" % subdir
    )

    if r.status_code != 200:
        r.raise_for_status()

    data = r.json()
    currvals = list(REMOVALS.get(subdir, []))
    for pkgs_section_key in ["packages", "packages.conda"]:
        for pkg_name in data.get(pkgs_section_key, []):
            currvals.append(pkg_name)

    instructions["remove"].extend(tuple(set(currvals)))


def _gen_patch_instructions(index, new_index, subdir):
    instructions = {
        "patch_instructions_version": 1,
        "packages": defaultdict(dict),
        "packages.conda": defaultdict(dict),
        "revoke": [],
        "remove": [],
    }

    _add_removals(instructions, subdir)

    # diff all items in the index and put any differences in the instructions
    for pkgs_section_key in ["packages", "packages.conda"]:
        for fn in index.get(pkgs_section_key, {}):
            assert fn in new_index[pkgs_section_key]

            # replace any old keys
            for key in index[pkgs_section_key][fn]:
                assert key in new_index[pkgs_section_key][fn], (key, index[pkgs_section_key][fn], new_index[pkgs_section_key][fn])
                if index[pkgs_section_key][fn][key] != new_index[pkgs_section_key][fn][key]:
                    instructions[pkgs_section_key][fn][key] = new_index[pkgs_section_key][fn][key]

            # add any new keys
            for key in new_index[pkgs_section_key][fn]:
                if key not in index[pkgs_section_key][fn]:
                    instructions[pkgs_section_key][fn][key] = new_index[pkgs_section_key][fn][key]

    return instructions


def has_dep(record, name):
    return any(dep.split(' ')[0] == name for dep in record.get('depends', ()))


def get_python_abi(version, subdir, build=None):
    if build is not None:
        m = re.match(r".*py\d\d", build)
        if m:
            version = f"{m.group()[-2]}.{m.group()[-1]}"
    if version.startswith("2.7"):
        if subdir.startswith("linux"):
            return "cp27mu"
        return "cp27m"
    elif version.startswith("2.6"):
        if subdir.startswith("linux"):
            return "cp26mu"
        return "cp26m"
    elif version.startswith("3.4"):
        return "cp34m"
    elif version.startswith("3.5"):
        return "cp35m"
    elif version.startswith("3.6"):
        return "cp36m"
    elif version.startswith("3.7"):
        return "cp37m"
    elif version.startswith("3.8"):
        return "cp38"
    elif version.startswith("3.9"):
        return "cp39"
    return None


# Workaround for https://github.com/conda/conda-build/pull/3868
def remove_python_abi(record):
    if record['name'] in ['python', 'python_abi', 'pypy']:
        return
    if not has_dep(record, 'python_abi'):
        return
    depends = record.get('depends', [])
    record['depends'] = [dep for dep in depends if dep.split(" ")[0] != "python_abi"]


changes = set([])

def add_python_abi(record, subdir):
    record_name = record['name']
    # Make existing python and python-dependent packages conflict with pypy
    if record_name == "python" and not record['build'].endswith("pypy"):
        version = record['version']
        new_constrains = record.get('constrains', [])
        python_abi = get_python_abi(version, subdir)
        new_constrains.append(f"python_abi * *_{python_abi}")
        record['constrains'] = new_constrains
        return

    if has_dep(record, 'python') and not has_dep(record, 'pypy') and not has_dep(record, 'python_abi'):
        python_abi = None
        new_constrains = record.get('constrains', [])
        build = record["build"]
        ver_strict_found = False
        ver_relax_found = False

        for dep in record.get('depends', []):
            dep_split = dep.split(' ')
            if dep_split[0] == 'python':
                if len(dep_split) == 3:
                    continue
                if len(dep_split) == 1:
                    continue
                elif dep_split[1] == "<3":
                    python_abi = get_python_abi("2.7", subdir, build)
                elif dep_split[1].startswith(">="):
                    m = CB_PIN_REGEX.match(dep_split[1])
                    if m == None:
                        python_abi = get_python_abi("", subdir, build)
                    else:
                        lower = pad_list(m.group("lower").split("."), 2)[:2]
                        upper = pad_list(m.group("upper").split("."), 2)[:2]
                        if lower[0] == upper[0] and int(lower[1]) + 1 == int(upper[1]):
                            python_abi = get_python_abi(m.group("lower"), subdir, build)
                        else:
                            python_abi = get_python_abi("", subdir, build)
                else:
                    python_abi = get_python_abi(dep_split[1], subdir, build)
                if python_abi:
                    new_constrains.append(f"python_abi * *_{python_abi}")
                    changes.add((dep, f"python_abi * *_{python_abi}"))
                    ver_strict_found = True
                else:
                    ver_relax_found = True
        if not ver_strict_found and ver_relax_found:
            new_constrains.append("pypy <0a0")
        record['constrains'] = new_constrains


def _gen_new_index(repodata, subdir):
    indexes = {}
    for index_key in ['packages', 'packages.conda']:
        indexes[index_key] = _gen_new_index_per_key(repodata, subdir, index_key)
        patch_yaml_edit_index(indexes[index_key], subdir)

    return indexes


def _gen_new_index_per_key(repodata, subdir, index_key):
    """Make any changes to the index by adjusting the values directly.

    This function returns the new index with the adjustments.
    Finally, the new and old indices are then diff'ed to produce the repo
    data patches.
    """
    index = copy.deepcopy(repodata[index_key])

    # deal with windows vc features
    if subdir.startswith("win-"):
        python_vc_deps = {
            '2.6': 'vc 9.*',
            '2.7': 'vc 9.*',
            '3.3': 'vc 10.*',
            '3.4': 'vc 10.*',
            '3.5': 'vc 14.*',
            '3.6': 'vc 14.*',
            '3.7': 'vc 14.*',
        }
        for fn, record in index.items():
            record_name = record['name']
            if record_name == 'python' and 'pypy' not in record['build']:
                # remove the track_features key
                if 'track_features' in record:
                    record['track_features'] = None
                # add a vc dependency
                if not any(d.startswith('vc') for d in record['depends']):
                    depends = record['depends']
                    depends.append(python_vc_deps[record['version'][:3]])
                    record['depends'] = depends
            elif 'vc' in record.get('features', ''):
                # remove vc from the features key
                vc_version = _extract_and_remove_vc_feature(record)
                if vc_version:
                    # add a vc dependency
                    if not any(d.startswith('vc') for d in record['depends']):
                        depends = record['depends']
                        depends.append('vc %d.*' % vc_version)
                        record['depends'] = depends

    for fn, record in index.items():
        record_name = record["name"]
        deps = record.get("depends", ())

        ########################################
        # Ecosystem-wide patches for changes in
        # metapackages, CI stuff, conda, etc.
        # Generally managed by conda-forge/core
        ########################################

        if "license" in record and "license_family" not in record and record["license"]:
            family = get_license_family(record["license"])
            if family:
                record['license_family'] = family

        if record.get('timestamp', 0) < 1604417730000:
            if subdir == 'noarch':
                remove_python_abi(record)
            else:
                add_python_abi(record, subdir)

        # add track_features to old python_abi pypy packages
        if (record_name == 'python_abi' and 'pypy' in record['build'] and
                "track_features" not in record):
            record["track_features"] = "pypy"

        # replace =2.7 with ==2.7.* for compatibility with older conda
        new_deps = []
        changed = False
        for dep in record.get("depends", []):
            dep_split = dep.split(" ")
            if len(dep_split) == 2 and dep_split[1].startswith("=") and not dep_split[1].startswith("=="):
                split_or = dep_split[1].split("|")
                split_or[0] = "=" + split_or[0] + ".*"
                new_dep = dep_split[0] + " " + "|".join(split_or)
                changed = True
            else:
                new_dep = dep
            new_deps.append(new_dep)
        if changed:
            record["depends"] = new_deps
        del new_deps
        del changed

        # make sure pybind11 and pybind11-global have run constraints on
        # the abi metapackage
        # see https://github.com/conda-forge/conda-forge-repodata-patches-feedstock/issues/104  # noqa
        if (
            record_name in ["pybind11", "pybind11-global"]
            # this version has a constraint sometimes
            and (
                parse_version(record["version"])
                <= parse_version("2.6.1")
            )
            and not any(
                c.startswith("pybind11-abi ")
                for c in record.get("constrains", [])
            )
        ):
            _add_pybind11_abi_constraint(fn, record)

        if record_name not in ["blas", "libblas", "libcblas", "liblapack",
                               "liblapacke", "lapack", "blas-devel"]:
            _replace_pin('liblapack >=3.8.0,<3.9.0a0', 'liblapack >=3.8.0,<4.0.0a0', deps, record)
            _replace_pin('liblapacke >=3.8.0,<3.9.0a0', 'liblapacke >=3.8.0,<4.0.0a0', deps, record)

        if record_name == "conda-forge-ci-setup" and record.get('timestamp', 0) < 1638899810000:
            constrains = record.get("constrains", [])
            found = any(c.startswith("boa") for c in constrains)
            if not found:
                constrains.append("boa >=0.8,<0.9")
            record["constrains"] = constrains

        if record_name == "boa" and record.get("timestamp", 0) <= 1619005998286:
            depends = record.get("depends", [])
            for i, dep in enumerate(depends):
                if dep.startswith("mamba") and "<" not in dep and ".*" not in dep:
                    _dep_parts = dep.split(" ")
                    _dep_parts[1] = _dep_parts[1] + ",<0.15a0"
                    depends[i] = " ".join(_dep_parts)
            record["depends"] = depends

        if record_name == "conda-lock" and record.get("timestamp", 0) < 1685186303000:
            assert "constrains" not in record
            record["constrains"] = ["urllib3 <2"]

        # conda-libmamba-solver uses calver YY.MM.micro
        if record_name == "conda-libmamba-solver":
            if record.get("timestamp", 0) <= 1669391735453:  # 2022-11-25
                # libmamba 0.23 introduces API breaking changes, pin to v0.22
                _replace_pin("libmambapy >=0.22", "libmambapy 0.22.*", record["depends"], record)
                # conda 22.11 introduces the plugin system, which needs a new release
                _replace_pin("conda >=4.12", "conda >=4.12,<22.11.0a", record["depends"], record)
                _replace_pin("conda >=4.13", "conda >=4.13,<22.11.0a", record["depends"], record)
            elif record.get("timestamp", 0) <= 1674230331000:  # 2023-01-20
                # conda 23.1 changed an internal SubdirData API needed with S3/FTP channels
                _replace_pin("conda >=22.11.0", "conda >=22.11.0,<23.1.0a", record["depends"], record)
            elif record.get("timestamp", 0) <= 1678721528000: # 2023-03-13:
                # conda 23.3 changed an internal SubdirData API needed with S3/FTP channels
                # conda deprecated Boltons leading to a breakage in the solver api interface
                _replace_pin("conda >=22.11.0", "conda >=22.11.0,<23.2.0a", record["depends"], record)

        if subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"] and \
            record_name in {"libmamba", "libmambapy"} \
            and record.get("version", 0) == "0.23.3":
            _replace_pin("libstdcxx-ng >=10.3.0", "libstdcxx-ng >=12.1.0", record["depends"], record)
            _replace_pin("libgcc-ng >=10.3.0", "libgcc-ng >=12.1.0", record["depends"], record)

        if record_name == "conda-build":
            # Code removed in conda 4.13.0 broke older conda-build releases;
            # x-ref issue: conda/conda-build#4481
            if (
                parse_version(record["version"]) <=
                parse_version("3.21.7") or
                # backported fix in 3.21.8, build 1
                # (PR: conda-forge/conda-build-feedstock#176)
                record["version"] == "3.21.8" and record["build_number"] == 0
            ):
                for i, dep in enumerate(record["depends"]):
                    dep_name, *dep_other = dep.split()
                    if dep_name == "conda" and ",<" not in dep:
                        record["depends"][i] = "{} {}<4.13.0".format(
                            dep_name, dep_other[0] + "," if dep_other else ""
                        )
            # pin setuptools to <66 to avoid `parse_version` issues
            # see https://github.com/conda-forge/conda-forge-pinning-feedstock/issues/3973
            if record.get("timestamp", 0) <= 1674131439051:  # 2023-01-19
                for i, dep in enumerate(record["depends"]):
                    dep_name, *dep_other = dep.split()
                    if dep_name == "setuptools" and ",<" not in dep:
                        record["depends"][i] = "{} {}<66.0.0a0".format(
                            dep_name, dep_other[0] + "," if dep_other else ""
                        )

        if (record_name == "conda" and
            record["version"] == "22.11.1" and
            record["build_number"] == 0):
            for i, dep in enumerate(record["constrains"]):
                dep_name, *dep_other = dep.split()
                if dep_name.startswith("conda-libmamba-solver"):
                    record["constrains"][i] = "conda-libmamba-solver >=22.12.0"
        if record_name == "mamba" and (
            parse_version(record["version"]) <
            parse_version("0.24.0") or (
                (parse_version(record["version"]) <
                 parse_version("0.24.0")) and (
                     record["build_number"] == 0)
                 )):
            for i, dep in enumerate(record["depends"]):
                dep_name, *dep_other = dep.split()
                if dep_name == "conda" and ",<" not in dep:
                    record["depends"][i] = "{} {}<4.13.0".format(
                        dep_name, dep_other[0] + "," if dep_other else ""
                        )
        if record_name == "mamba" and (
            parse_version(record["version"]) ==
            parse_version("0.24.0")) and (
                record["build_number"] == 1):

            for i, dep in enumerate(record["depends"]):
                dep_name, *dep_other = dep.split()
                if dep_name == "conda":
                    record["depends"][i] = "conda >=4.8"

        if record_name == "mamba" and (
            parse_version(record["version"]) ==
            parse_version("0.25.0")):

            for i, dep in enumerate(record["depends"]):
                dep_name, *dep_other = dep.split()
                if dep_name == "conda":
                    record["depends"][i] = "conda >=4.8,<5"

        if record_name == "anaconda-client":
            # Bump minimum `requests` requirement of `anaconda-client` 1.11.0
            # https://github.com/conda-forge/anaconda-client-feedstock/pull/35
            if (
            parse_version(record["version"]) ==
            parse_version("1.11.0")):
                i = -1
                deps = record["depends"]
                with suppress(ValueError):
                    i = deps.index("requests >=2.9.1")
                if i >= 0:
                    deps[i] = "requests >=2.20.0"
            if record.get("timestamp", 0) <= 1684878992896:  # 2023-05-23
                # https://github.com/conda-forge/conda-forge-ci-setup-feedstock/issues/242
                # https://github.com/conda-forge/anaconda-client-feedstock/issues/40
                if any("urllib3" in dep for dep in record["depends"]):
                    _replace_pin(
                        "urllib3 >=1.26.4",
                        "urllib3 >=1.26.4,<2.0.0a0",
                        record["depends"],
                        record,
                    )
                else:
                    # old versions depended on urllib3 via requests;
                    # requests 2.30+ allows urllib3 2.x
                    for lower_bound in (">=2.9.1", ">=2.0", ">=2.20.0"):
                        _replace_pin(
                            f"requests {lower_bound}",
                            f"requests {lower_bound},<2.30.0a0",
                            record["depends"],
                            record,
                        )
            # https://github.com/conda-forge/anaconda-client-feedstock/pull/44
            # https://github.com/Anaconda-Platform/anaconda-client/issues/678
            if (
                parse_version(record["version"])
                == parse_version("1.12.0")
            ) and record["build_number"] == 0:
                # Guard python-dateutil dependency with trailing space in "python "
                python_pinning = [x for x in record["depends"] if x.startswith("python ")]
                for pinning in python_pinning:
                    _replace_pin(pinning, "python >=3.8", record["depends"], record)

        if record_name == "conda-build":
            # conda-build 3.26.x requires conda 23.7.x
            if record["version"] in ("3.26.0", "3.26.1") and record.get("timestamp", 0) <= 16935094895456:
                _replace_pin("conda >=4.13", "conda >=23.7.3", record["depends"], record)

        ############################################
        # Compilers, Runtimes and Related Patches
        ############################################

        if record_name == "vs2015_runtime" and record.get('timestamp', 0) < 1633470721000:
            pversion = parse_version(record['version'])
            vs2019_version = parse_version('14.29.30037')
            if pversion < vs2019_version:
                # make these conflict with ucrt
                new_constrains = record.get("constrains", [])
                new_constrains.append("ucrt <0a0")
                record['constrains'] = new_constrains

        # fix only packages built before the run_exports was corrected.
        if any(dep == "libflang" or dep.startswith("libflang >=5.0.0") for dep in deps) and record.get('timestamp', 0) < 1611789153000:
            record["depends"].append("libflang <6.0.0.a0")

        llvm_pkgs = ["clang", "clang-tools", "llvm", "llvm-tools", "llvmdev"]
        if record_name in llvm_pkgs:
            new_constrains = record.get('constrains', [])
            version = record["version"]
            for pkg in llvm_pkgs:
                if record_name == pkg:
                    continue
                if pkg in new_constrains:
                    del new_constrains[pkg]
                if any(constraint.startswith(f"{pkg} ") for constraint in new_constrains):
                    continue
                new_constrains.append(f'{pkg} {version}.*')
            record['constrains'] = new_constrains

        if record_name == "gcc_impl_{}".format(subdir):
            _relax_exact(fn, record, "binutils_impl_{}".format(subdir))

        # some symlinks changed in gfortran, so we need to adjust things
        # plus we missed a key version constraint
        if (
            subdir in ["osx-64", "osx-arm64"]
            and record_name == "gfortran"
        ):
            for i, dep in enumerate(record["depends"]):
                if dep == f"gfortran_{subdir}":
                    record["depends"][i] = dep + " ==" + record["version"]

        # make sure the libgfortran version is bound from 3 to 4 for osx
        if subdir == "osx-64":
            _fix_libgfortran(fn, record)
            _fix_libcxx(fn, record)

            full_pkg_name = fn.replace('.tar.bz2', '')
            if full_pkg_name in OSX_SDK_FIXES:
                _set_osx_virt_min(fn, record, OSX_SDK_FIXES[full_pkg_name])

        # when making the glibc 2.28 sysroots, we found we needed to go back
        # and add the current repodata hack packages to the cos7 sysroots
        # for aarch64, ppc64le and s390x
        for __subdir in ["linux-s390x", "linux-aarch64", "linux-ppc64le"]:
            if (
                record_name in [
                    "kernel-headers_" + __subdir, "sysroot_" + __subdir
                ]
                and record.get('timestamp', 0) < 1682273081000  # 2023-04-23
                and record["version"] == "2.17"
            ):
                new_depends = record.get("depends", [])
                new_depends.append(
                    "_sysroot_" + __subdir + "_curr_repodata_hack 4.*"
                )
                record["depends"] = new_depends

        # make old binutils packages conflict with the new sysroot packages
        # that have renamed the sysroot from conda_cos6 or conda_cos7 to just
        # conda
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "binutils", "binutils_impl_" + subdir, "ld_impl_" + subdir]
            and record.get('timestamp', 0) < 1589953178153  # 2020-05-20
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # make sure the old compilers conflict with the new sysroot packages
        # and they only use libraries from the old compilers
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record['version'] in ['5.4.0', '7.2.0', '7.3.0', '8.2.0']
        ):
            new_constrains = record.get('constrains', [])
            for pkg in ["libgcc-ng", "libstdcxx-ng", "libgfortran", "libgomp"]:
                new_constrains.append("{} 5.4.*|7.2.*|7.3.*|8.2.*|9.1.*|9.2.*".format(pkg))
            new_constrains.append("binutils_impl_" + subdir + " <2.34")
            new_constrains.append("ld_impl_" + subdir + " <2.34")
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # we pushed a few builds of the compilers past the list of versions
        # above which do not use the sysroot packages - this block catches those
        # it will also break some test builds of the new compilers but we should
        # not be using those anyways and they are marked as broken.
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_impl_" + subdir, "gxx_impl_" + subdir, "gfortran_impl_" + subdir]
            and record['version'] not in ['5.4.0', '7.2.0', '7.3.0', '8.2.0']
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get('timestamp', 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        # all ctng activation packages that don't depend on the sysroot_*
        # packages are not compatible with the new sysroot_*-based compilers
        # root and cling must also be included as they have a builtin C++ interpreter
        if (
            subdir in ["linux-64", "linux-aarch64", "linux-ppc64le"]
            and record_name in [
                "gcc_" + subdir, "gxx_" + subdir, "gfortran_" + subdir,
                "binutils_" + subdir, "gcc_bootstrap_" + subdir, "root_base", "cling"]
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
            and record.get('timestamp', 0) < 1626220800000  # 2020-07-14
        ):
            new_constrains = record.get('constrains', [])
            new_constrains.append("sysroot_" + subdir + " ==99999999999")
            record["constrains"] = new_constrains

        if (record_name == "gcc_impl_{}".format(subdir)
            and record['version'] in ['5.4.0', '7.2.0', '7.3.0', '8.2.0', '8.4.0', '9.3.0']
            and record.get('timestamp', 0) < 1627530043000  # 2021-07-29
        ):
            new_depends = record.get("depends", [])
            new_depends.append("libgcc-ng <=9.3.0")
            record["depends"] = new_depends

        # old CDTs with the conda_cos6 or conda_cos7 name in the sysroot need to
        # conflict with the new CDT and compiler packages
        # all of the new CDTs and compilers depend on the sysroot_{subdir} packages
        # so we use a constraint on those
        if (
            subdir == "noarch"
            and (
                record_name.endswith("-cos6-x86_64") or
                record_name.endswith("-cos7-x86_64") or
                record_name.endswith("-cos7-aarch64") or
                record_name.endswith("-cos7-ppc64le")
            )
            and not record_name.startswith("sysroot-")
            and not any(__r.startswith("sysroot_") for __r in record.get("depends", []))
        ):
            if record_name.endswith("x86_64"):
                sys_subdir = "linux-64"
            elif record_name.endswith("aarch64"):
                sys_subdir = "linux-aarch64"
            elif record_name.endswith("ppc64le"):
                sys_subdir = "linux-ppc64le"

            new_constrains = record.get('constrains', [])
            if not any(__r.startswith("sysroot_") for __r in new_constrains):
                new_constrains.append("sysroot_" + sys_subdir + " ==99999999999")
                record["constrains"] = new_constrains

        llvm_pkgs = ["libclang", "clang", "clang-tools", "llvm", "llvm-tools", "llvmdev"]
        for llvm in ["libllvm8", "libllvm9"]:
            if any(dep.startswith(llvm) for dep in deps):
                if record_name not in llvm_pkgs:
                    _relax_exact(fn, record, llvm, max_pin="x.x")
                else:
                    _relax_exact(fn, record, llvm, max_pin="x.x.x")

        # Properly depend on clangdev 5.0.0 flang* for flang 5.0
        if record_name == "flang":
            deps = record["depends"]
            if record['version'] == "5.0.0":
                deps += ["clangdev * flang*"]

        # add as run_constrained for cling
        if (
            record_name == "cling"
            and record['version'] >= "0.8"
        ):
            record.setdefault('constrains', []).extend((
                "gxx_linux-64 !=9.5.0",
            ))

        ############################################
        # CUDA Ecosystem Patches
        ############################################
        deps = record.get("depends", ())
        i = -1
        with suppress(ValueError):
            i = deps.index("cudatoolkit 11.2|11.2.*")
        if i >= 0:
            deps[i] = "cudatoolkit >=11.2,<12.0a0"

        if record_name == "cuda-version" and record['build_number'] < 2 and record.get('timestamp', 0) < 1683211961000:
            cuda_major_minor = ".".join(record["version"].split(".")[:2])
            constrains = record.get('constrains', [])
            for i, c in enumerate(constrains):
                if c.startswith('cudatoolkit'):
                    constrains[i] = f'cudatoolkit {cuda_major_minor}|{cuda_major_minor}.*'
                    break
            else:
                constrains.append( f'cudatoolkit {cuda_major_minor}|{cuda_major_minor}.*' )
            record['constrains'] = constrains

        if record_name == "nccl" and 1681282800000 < record.get("timestamp", 0) < 1686034800000:
            deps = record.get("depends", [])
            for i in range(len(deps)):
                dep = deps[i]
                if dep.startswith("cudatoolkit"):
                    spec = dep[11:]
                    dep = f"__cuda{spec}"
                deps[i] = dep

        if record_name == "ucx" and record.get('timestamp', 0) < 1682924400000:
            constrains = record.get('constrains', [])
            for i, c in enumerate(constrains):
                if c.startswith('cudatoolkit'):
                    v = c.split()[-1]
                    if v != '>=11.2,<12':
                        constrains[i] = c = f'cudatoolkit {v}|{v}.*'
            record['constrains'] = constrains

        # cuTENSOR 1.3.x is binary incompatible with 1.2.x. Let's just pin exactly since
        # it appears semantic versioning is not guaranteed.
        _replace_pin("cutensor >=1.2.2.5,<2.0a0", "cutensor ==1.2.2.5", deps, record)
        _replace_pin("cutensor >=1.2.2.5,<2.0a0", "cutensor ==1.2.2.5", record.get("constrains", []), record, target='constrains')

        # libcugraph 0.19.0 is compatible with the new calver based version 21.x
        if record_name == "cupy":
            _replace_pin("libcugraph >=0.19.0,<1.0a0", "libcugraph >=0.19.0", record.get("constrains", []), record, target='constrains')

        ############################################
        # Custom Patches that cannot be YAML-ized
        ############################################

        # TensorFlow Probability was published with loose constraints on TensorFlow-base leading to broken dependencies.
        # Each release actually specifies the exact version of TensorFlow and JAX that it supports, therefore we need to
        # pin the dependencies to the exact version that was used to build the package.
        # See also issue:
        if (record.get("timestamp", 0) < 1676674332000) and (record_name == "tensorflow-probability"):
            version_matrix = {
                "0.17.0": {"tensorflow-base": ">=2.9,<2.10", "jax": ">=0.3.13,<0.4.0"},
                "0.15.0": {"tensorflow-base": ">=2.7,<2.8", "jax": ">=0.2.21,<0.3.0"},  # actual jax minimum not mention in release notes
                "0.14.1": {"tensorflow-base": ">=2.6,<2.7", "jax": ">=0.2.21,<0.3.0"},
                "0.14.0": {"tensorflow-base": ">=2.6,<2.7", "jax": ">=0.2.20,<0.3.0"},
                "0.13.0": {"tensorflow-base": ">=2.5,<2.6"},  # no JAX as it isn't mentioned anymore, is it needed to re-add?
                "0.12.2": {"tensorflow-base": ">=2.4,<2.5"},
                "0.12.1": {"tensorflow-base": ">=2.4,<2.5"},
                "0.12.0": {"tensorflow-base": ">=2.4,<2.5"},
                "0.10.1": {"tensorflow-base": ">=2.2,<2.3"},
                "0.10.0": {"tensorflow-base": ">=2.2,<2.3"},
                "0.8.0": {"tensorflow-base": ">=1.15,<2.1"},
                # Older versions are TF V1, too old to bother with but restricting them to <2 s.t. the solver doesn't pick them up
                "0.7": {"tensorflow-base": ">=1.13.1,<2"},
                "0.6.0": {"tensorflow-base": ">=1.13.1,<2"},
                "0.5.0": {"tensorflow-base": ">=1.11.0,<2"},

            }
            version = record["version"]
            if version in version_matrix:
                deps = version_matrix[version]
                dependencies = record['depends']
                for newdep, newrequ in deps.items():
                    found = False
                    for i, curdep in enumerate(dependencies):
                        curdep_pkg = curdep.split(" ")[0]
                        if curdep_pkg == 'tensorflow':  # remove it, will be replaced with tf-base if needed
                            del dependencies[i]
                        elif curdep_pkg == newdep:
                            found = True
                            dependencies[i] = f'{newdep} {newrequ}'
                            # NO break, the loop needs also to make sure that all the tensorflow deps are removed.
                    if not found:  # It wasn't in the dependencies so we add it
                        dependencies.append(f'{newdep} {newrequ}')

        if record_name == 'dask':
            deps = record.get("depends", ())

            # older versions of dask are incompatible with bokeh=3
            # https://github.com/dask/community/issues/283#issuecomment-1295095683
            if record.get('timestamp', 0) < 1667000131632:  # releases prior to 2022.10.1
                bokeh_pinning = [x for x in record['depends'] if x.startswith('bokeh')]
                if bokeh_pinning:
                    bokeh_pinning = bokeh_pinning[0]
                    _replace_pin(
                        bokeh_pinning,
                        bokeh_pinning + (",<3" if bokeh_pinning[-1].isdigit() else " <3"),
                        deps,
                        record
                    )

            # older versions of dask are incompatible with pandas=2
            if record.get('timestamp', 0) < 1676063992630:  # releases prior to 2023.2.0
                pandas_pinning = [x for x in record['depends'] if x.startswith('pandas')]
                if pandas_pinning:
                    pandas_pinning = pandas_pinning[0]
                    _replace_pin(
                        pandas_pinning,
                        pandas_pinning + (",<2" if pandas_pinning[-1].isdigit() else " <2"),
                        deps,
                        record
                    )

        if record_name in {"distributed", "dask"}:
            version = parse_version(record["version"])
            if (
                version >= parse_version("2021.12.0") and
                version < parse_version("2022.8.0") or
                version == parse_version("2022.8.0") and
                record["build_number"] < 2
            ):
                for dep in record["depends"]:
                    if dep.startswith("dask-core") or dep.startswith("distributed"):
                        pkg = dep.split()[0]
                        major_minor_patch = record["version"].split(".")
                        major_minor_patch[2] = str(int(major_minor_patch[2]) + 1)
                        next_patch_version = ".".join(major_minor_patch)
                        _replace_pin(
                            dep, f"{pkg} >={version},<{next_patch_version}.0a0", record["depends"], record
                        )

        deps = record.get("depends", ())
        if (
            record_name in {"slepc", "petsc4py", "slepc4py"}
            and record.get("timestamp", 0) < 1657407373000
            and record.get("version").startswith("3.17.")
        ):
            # rename scalar pins to workaround conda bug #11612
            for dep in list(deps):
                dep_name, *version_build = dep.split()
                if dep_name not in {"petsc", "slepc", "petsc4py"}:
                    continue
                if len(version_build) < 2:
                    # version only, no build pin
                    continue
                version_pin, build_pin = version_build[:2]
                for scalar in ("real", "complex"):
                    old_build = f"*{scalar}*"
                    if build_pin == f"*{scalar}*":
                        new_build = f"{scalar}_*"
                        new_dep = f"{dep_name} {version_pin} {new_build}"
                        _replace_pin(dep, new_dep, deps, record)

        # FIXME: this one is buggy
        if record.get('timestamp', 0) < 1663795137000:
            if any(dep.startswith("pango >=5.2") for dep in deps):
                _pin_looser(fn, record, "xz", max_pin="x")

        # this doesn't seem to match the _pin_looser or _pin_stricter patterns
        # nor _replace_pin
        if record_name == "jedi" and record.get("timestamp", 0) < 1592619891258:
            for i, dep in enumerate(record["depends"]):
                if dep.startswith("parso") and "<" not in dep:
                    _dep_parts = dep.split(" ")
                    _dep_parts[1] = _dep_parts[1] + ",<0.8.0"
                    record["depends"][i] = " ".join(_dep_parts)

        # FIXME: disable patching-out blas_openblas feature
        # because hotfixes are not applied to gcc7 label
        # causing inconsistent behavior
        # if (record_name == "blas" and
        #         record["track_features"] == "blas_openblas"):
        #     instructions["packages"][fn]["track_features"] = None
        # if "features" in record:
            # if "blas_openblas" in record["features"]:
            #     # remove blas_openblas feature
            #     instructions["packages"][fn]["features"] = _extract_feature(
            #         record, "blas_openblas")
            #     if not any(d.startswith("blas ") for d in record["depends"]):
            #         depends = record['depends']
            #         depends.append("blas 1.* openblas")
            #         instructions["packages"][fn]["depends"] = depends

        # remove features for openjdk and rb2
        if ("track_features" in record and
                record['track_features'] is not None):
            for feat in record["track_features"].split():
                if feat.startswith("openjdk"):
                    record["track_features"] = _extract_track_feature(
                        record, feat)

        # Patch bokeh version restrictions on older panels.
        if record_name == "panel":
            deps = record.get("depends", [])
            bokeh_dep = None
            if record["version"] in ["0.1.2", "0.1.3"]:
                bokeh_dep = "bokeh ==0.12.15"
            elif record["version"] in ["0.3.1", "0.4.0"]:
                bokeh_dep = "bokeh >=1.0.0,<1.1.0"
            elif record["version"] in ["0.5.1", "0.6.0"]:
                bokeh_dep = "bokeh >=1.1.0,<1.2.0"
            elif record["version"] in ["0.6.2", "0.6.3", "0.6.4"]:
                bokeh_dep = "bokeh >=1.3.0,<1.4.0"
            elif record["version"] in ["0.7.0"]:
                bokeh_dep = "bokeh >=1.4.0,<1.5.0"
            elif record["version"] in ["0.9.1", "0.9.2", "0.9.3", "0.9.4", "0.9.5"]:
                bokeh_dep = "bokeh >=2.0,<2.1"
            elif record["version"] in ["0.9.6", "0.9.7"]:
                bokeh_dep = "bokeh >=2.1,<2.2"
            elif record["version"] in ["0.10.0", "0.10.1", "0.10.2", "0.10.3"]:
                bokeh_dep = "bokeh >=2.2,<2.3"
            if bokeh_dep:
                deps = record.get("depends", [])
                ind = [deps.index(dep) for dep in deps if dep.startswith("bokeh")]
                if len(ind) == 1:
                    deps[ind[0]] = bokeh_dep
                else:
                    deps.append(bokeh_dep)
                record["depends"] = deps

        # FIXME: this one could be yaml but would be quite verbose
        if record_name == "dask-sql":
            # retroactively pin dask dependency for older version of dask-sql as it is now being pinned
            # https://github.com/dask-contrib/dask-sql/issues/302
            dask_sql_map = {"0.1.0rc2": "2.26.0", "0.1.2": "2.30.0", "0.2.0": "2.30.0", "0.2.2": "2.30.0",
                            "0.3.0": "2021.1.0", "0.3.1": "2021.2.0", "0.3.2": "2021.4.0", "0.3.3": "2021.4.1",
                            "0.3.4": "2021.4.1", "0.3.6": "2021.5.0", "0.3.9": "2021.8.0", "0.4.0": "2021.10.0"}
            if record["version"] in ["0.1.0rc2", "0.1.2", "0.2.0", "0.2.2", "0.3.0", "0.3.1"]:
                _replace_pin("dask >=2.19.0", f"dask =={dask_sql_map[record['version']]}", deps, record)
            if record["version"] in ["0.3.2", "0.3.3"]:
                _replace_pin("dask >=2.19.0,<=2021.2.0", f"dask =={dask_sql_map[record['version']]}", deps, record)
            if record["version"] in ["0.3.4", "0.3.6", "0.3.9", "0.4.0"]:
                _replace_pin("dask >=2.19.0,!=2021.3.0", f"dask =={dask_sql_map[record['version']]}", deps, record)

            # make dask/uvicorn pinnings consistent for older builds of 2022.10.1
            # https://github.com/conda-forge/dask-sql-feedstock/pull/46#issuecomment-1291416642
            if record["version"] == "2022.10.1" and record["build_number"] == 0:
                _replace_pin("dask >=2022.3.0,<=2022.9.2", "dask >=2022.3.0,<=2022.10.0", deps, record)
                _replace_pin("uvicorn >=0.11.3", "uvicorn >=0.13.4", deps, record)

        if record_name == "dask-cuda":
            timestamp = record.get("timestamp", 0)
            # older versions of dask-cuda do not work on non-UNIX operating systems and must be constrained to UNIX
            # issues in click 8.1.0 cause failures for older versions of dask-cuda
            if timestamp <= 1645130882435:  # 22.2.0 and prior
                new_depends = record.get("depends", [])
                new_depends += ["click ==8.0.4", "__linux"]
                record["depends"] = new_depends

            # older versions of dask-cuda do not work with pynvml 11.5+
            if timestamp <= 1676966400000:  # 23.2.0 and prior
                depends = record.get("depends", [])
                new_depends = [d + ",<11.5" if d.startswith("pynvml") else d
                               for d in depends]
                record["depends"] = new_depends

            # older versions of dask-cuda pulling in pandas are incompatible with pandas 2.0 and must be constrained to pandas 1
            if timestamp <= 1677122851413 and timestamp >= 1670873028930: # 22.12 to 23.2.1
                _replace_pin("pandas >=1.0", "pandas >=1.0,<1.6.0dev0", record["depends"], record)

            # there are various inconsistencies between the pinnings of dask-cuda on `rapidsai` and `conda-forge`,
            # this makes the packages roughly consistent while also removing the python upper bound where present
            if record["version"] == "0.18.0":
                _replace_pin("dask >=2.9.0", "dask >=2.4.0,<=2.22.0", record["depends"], record)
            elif record["version"] == "0.19.0":
                _replace_pin("dask >=2.9.0", "dask >=2.22.0,<=2021.4.0", record["depends"], record)
                _replace_pin("distributed >=2.18.0", "distributed >=2.22.0,<=2021.4.0", record["depends"], record)
            elif record["version"] == "21.6.0":
                _replace_pin("distributed >=2.22.0,<=2021.5.1", "distributed >=2.22.0,<2021.5.1", record["depends"], record)
            elif record["version"] in ("21.10.0", "22.2.0"):
                _replace_pin("pynvml >=11.0.0", "pynvml >=8.0.3", record["depends"], record)
            elif record["version"] == "22.4.0":
                _replace_pin("python >=3.8,<3.10", "python >=3.8", record["depends"], record)

        if record_name == "tsnecuda":
            # These have dependencies like
            # - libfaiss * *_cuda
            # - libfaiss * *cuda
            # which conda doesn't like
            deps = record.get("depends", [])
            for i in range(len(deps)):
                dep = deps[i]
                if dep.startswith("libfaiss") and dep.endswith("*cuda"):
                    dep = dep.replace("*cuda", "*_cuda")
                deps[i] = dep
            record["depends"] = deps

        if record_name == "proplot" and record.get("timestamp", 0) < 1634670686970:
            depends = record.get("depends", [])
            for i, dep in enumerate(depends):
                if dep.startswith("matplotlib"):
                    _dep_parts = dep.split(" ")
                    if len(_dep_parts) > 1:
                        _dep_parts[1] = _dep_parts[1] + ",<3.5.0a0"
                    else:
                        _dep_parts = list(_dep_parts) + ["<3.5.0a0"]
                    depends[i] = " ".join(_dep_parts)
                record["depends"] = depends

        if (
            record_name == "des-pizza-cutter-metadetect"
            and record.get("timestamp", 0) <= 1651245289563  # 2022/04/29
        ):
            if any(d == "metadetect" for d in record["depends"]):
                i = record["depends"].index("metadetect")
                record["depends"][i] = "metadetect <0.7.0.a0"
            else:
                for i in range(len(record["depends"])):
                    d = record["depends"][i]
                    if not d.startswith("metadetect "):
                        continue
                    d = d.split(" ")
                    if "<" in d[1]:
                        _pin_stricter(fn, record, "metadetect", "x.x", "0.7.0")
                    else:
                        record["depends"][i] = record["depends"][i] + ",<0.7.0.a0"

        if (
            record_name == "metadetect"
            and record.get("timestamp", 0) <= 1651593228024  # 2022/05
        ):
            if any(d == "ngmix" for d in record["depends"]):
                i = record["depends"].index("ngmix")
                record["depends"][i] = "ngmix <2.1.0a0"
            else:
                for i in range(len(record["depends"])):
                    d = record["depends"][i]
                    if not d.startswith("ngmix "):
                        continue
                    d = d.split(" ")
                    if "<" in d[1]:
                        _pin_stricter(fn, record, "ngmix", "x.x.x", "2.1.0")
                    else:
                        record["depends"][i] = record["depends"][i] + ",<2.1.0a0"

        ############################################
        # Patches that still need to be YAML-ized
        ############################################

        if (record_name == "keyring" and
                record["version"] == "23.6.0" and
                record["build_number"] == 0):
            for i, dep in enumerate(record["depends"]):
                dep_name = dep.split()[0]
                if dep_name == "importlib_metadata" and ">=" not in dep:
                    record["depends"][i] = "importlib_metadata >=3.6"

        if record_name == "constructor":
            # constructor 2.x incompatible with conda 4.6+
            # see https://github.com/jaimergp/anaconda-repodata-hotfixes/blob/229c10f6/main.py#L834
            if int(record["version"].split(".")[0]) < 3:
                _replace_pin("conda", "conda <4.6.0a0", record["depends"], record)
            # Pin NSIS on constructor
            # https://github.com/conda/constructor/issues/526
            if record.get("timestamp", 0) <= 1658913358571:
                _replace_pin("nsis >=3.01", "nsis 3.01", record["depends"], record)
            # conda 23.1 broke constructor
            # https://github.com/conda/constructor/pull/627
            if record.get("timestamp", 0) <= 1674637311000:
                _replace_pin("conda >=4.6", "conda >=4.6,<23.1.0a0", record["depends"], record)


        if (record_name == "grpcio-status" and
                record["version"] == "1.48.0" and
                record["build_number"] == 0):
            for i, dep in enumerate(record["depends"]):
                if dep == 'grpcio >=1.46.3':
                    record["depends"][i] = "grpcio >=1.48.0"

        if record_name == "cylc-rose" and (
            parse_version(record["version"]) <
            parse_version("0.3")
        ):
            for i, dep in enumerate(record["depends"]):
                dep_name = dep.split(" ", 1)[0]
                if dep_name in {"cylc-flow", "metomi-rose"}:
                    record["depends"][i] = dep.replace(">", "=", 1)

        # Different patch versions of foonathan-memory have different library names
        # See https://github.com/conda-forge/foonathan-memory-feedstock/pull/7
        if has_dep(record, "foonathan-memory") and record.get('timestamp', 0) < 1661242172938:
            _pin_stricter(fn, record, "foonathan-memory", "x.x.x")

        # The run_exports of antic on macOS were too loose. We add a stricter
        # pin on all packages built against antic before this was fixed.
        if record_name in ["libeantic", "e-antic"] and subdir.startswith("osx") and record.get("timestamp", 0) <= 1653062891029:
            _pin_stricter(fn, record, "antic", "x.x.x")

        if (record_name == "virtualenv" and
                record["version"] == "20.16.3" and
                record["build_number"] == 0):
            new_deps = []
            for dep in record["depends"]:
                if dep == "distlib >=0.3.1,<1":
                    dep = "distlib >=0.3.5,<1"
                elif dep == "filelock >=3.2,<4":
                    dep = "filelock >=3.4.1,<4"
                elif dep == "platformdirs >=2,<3":
                    dep = "platformdirs >=2.4,<3"
                elif dep == "six >=1.9.0,<2":
                    dep = None
                elif dep == "importlib-metadata >=0.12":
                    dep = "importlib-metadata >=4.8.3"

                if dep is not None:
                    new_deps.append(dep)
            record["depends"] = new_deps

        # ipykernel >=4.0.1,<6.5.0 needs ipython_genutils. Old versions of
        # ipython and traitlets depend on ipython_genutils so the dependency
        # was originally satisfied indirectly. Newer versions of ipython and
        # traitlets don't pull in ipython_genutils anymore so we need to make
        # that dependency explicit.
        if (record_name == "ipykernel" and record.get("timestamp", 0) <= 1664184744000 and
                parse_version("4.0.1") <=
                parse_version(record["version"]) < parse_version("6.5.0")):
            for dep in record["depends"]:
                if dep.startswith("ipython_genutils"):
                    break
            else:
                # Any version of ipython_genutils will do. The package is not
                # developed anymore since it has been dropped by all its consumers.
                record["depends"].append("ipython_genutils >=0.2.0")

        if (any(depend.startswith("openh264 >=2.3.0,<2.4")
                for depend in record['depends']) or
            any(depend.startswith("openh264 >=2.3.1,<2.4")
                for depend in record['depends'])):
            _pin_stricter(fn, record, "openh264", "x.x.x")

        if (record_name == "thrift_sasl" and
                record["version"] == "0.4.3" and
                record["build_number"] == 0):
            new_deps = []
            six_found = False
            for dep in record["depends"]:
                if dep in ["pure-sasl", "sasl"]:
                    dep = "pure-sasl >=0.6.2"
                if 'six' in dep:
                    six_found = True
                new_deps.append(dep)
            if not six_found:
                new_deps.append("six >=1.13.0")
            record["depends"] = new_deps

        if (record_name == "thrift_sasl" and
                record["version"] == "0.4.3" and
                record["build_number"] == 1):
            new_deps = []
            for dep in record["depends"]:
                if dep == "thrift >=0.13":
                    dep = "thrift >=0.10.0"
                new_deps.append(dep)
            record["depends"] = new_deps

        # jinja2 3 breaks nbconvert 5
        # see https://github.com/conda-forge/nbconvert-feedstock/issues/81
        # the issue there says to pin mistune <1. However some current mistune
        # pins for v5 are <2, so going with that.
        if (
            record_name == "nbconvert"
            and parse_version(record["version"]).major == 5
        ):
            for i in range(len(record["depends"])):
                parts = record["depends"][i].split(" ")
                if parts[0] == "jinja2":
                    if len(parts) == 1:
                        parts.append("<3a0")
                    elif len(parts) == 2 and "<" not in parts[1]:
                        parts[1] = parts[1] + ",<3a0"
                    record["depends"][i] = " ".join(parts)
                elif parts[0] == "mistune":
                    if len(parts) == 2 and "<" not in parts[1]:
                        parts[1] = parts[1] + ",<2a0"
                    record["depends"][i] = " ".join(parts)

        # nbconvert(-core) did not provide top pins of pandoc until 7.2.1=*_1
        # see https://github.com/conda-forge/nbconvert-feedstock/issues/94
        # fixed in https://github.com/conda-forge/nbconvert-feedstock/pull/96
        if (
            record.get("timestamp", 0) <= 1680046165000
            and record_name in ["nbconvert", "nbconvert-core"]
            and (
                parse_version(record["version"]) <
                parse_version("7.2.2")
            )
        ):
            nbconvert_version = parse_version(record["version"])
            for field in ["depends", "constrains"]:
                for i in range(len(record.get(field, []))):
                    parts = record[field][i].split(" ")
                    if parts[0] == "pandoc":
                        if nbconvert_version < parse_version("5.5.0"):
                            parts = [parts[0], ">=1.12.1,<2.0.0"]
                        elif (
                            nbconvert_version < parse_version("7.2.1")
                        ) or (
                            nbconvert_version == parse_version("7.2.1")
                            and record["build_number"] < 1
                        ):
                            parts = [parts[0], ">=1.12.1,<3.0.0"]
                        record[field][i] = " ".join(parts)

        # selenium 4.10 removes code used by robotframework-seleniumlibrary <6.1.1
        if (
            record.get("timestamp", 0) <= 1686323537000
            and record_name == "robotframework-seleniumlibrary"
            and (
                parse_version(record["version"]) <=
                parse_version("6.1.0")
            )
        ):
            for i in range(len(record["depends"])):
                parts = record["depends"][i].split(" ")
                if parts[0] == "selenium":
                    if len(parts) == 2 and "<" not in parts[1]:
                        parts[1] = parts[1] + ",<4.10"
                    record["depends"][i] = " ".join(parts)

        # conda moved to calvar from semver and this broke old versions of
        # conda smithy that do on-the-fly version checks
        if (
            record_name == "conda-smithy"
            and (
                parse_version(record["version"]) <=
                parse_version("3.21.1")
            )
        ):
            for i in range(len(record["depends"])):
                parts = record["depends"][i].split(" ")
                if parts[0] == "conda":
                    if len(parts) == 1:
                        parts.append("<5a0")
                    elif len(parts) == 2 and "<" not in parts[1]:
                        parts[1] = parts[1] + ",<5a0"
                    record["depends"][i] = " ".join(parts)

        if (
                record_name == "satpy"
                and record.get("timestamp", 0) <= 1665672000000
                and record["build_number"] == 0
                and (parse_version(record["version"]) == parse_version("0.37.0")
                or parse_version(record["version"]) == parse_version("0.37.1"))
                ):
            _replace_pin("python >=3.7", "python >=3.8", record["depends"], record)

        # `python-slugify` clobbers these other, unmaintained `slugify`s in lib and bin
        if record_name == "python-slugify":
            record.setdefault('constrains', []).extend([
                "slugify <0",
                "awesome-slugify <0",
            ])

        # Flake8 6 removed some deprecated option parsing APIs and broke these plugins
        if ((record_name == 'flake8-copyright'
             and parse_version(record['version']) <= parse_version('0.2.3'))
            or (record_name == 'flake8-quotes'
             and parse_version(record['version']) <= parse_version('3.3.1'))):
            _replace_pin("flake8", "flake8 <6", record["depends"], record)

        # NetworkX 2.7.1 build 0 had wrong dependency information
        # This was fixed in https://github.com/conda-forge/networkx-feedstock/pull/32
        # This patches build 0 with the right information too.
        if (
            record_name == "networkx"
            and record["version"] == "2.7.1"
            and record["build_number"] == 0
        ):
            _replace_pin("python >=3.6", "python >=3.8", record["depends"], record)
            _replace_pin(
                "scipy >=1.5,!=1.6.1", "scipy >=1.8", record["depends"], record
            )
            _replace_pin(
                "matplotlib-base >=3.3",
                "matplotlib-base >=3.4",
                record["depends"],
                record,
            )
            _replace_pin("pandas >=1.1", "pandas >=1.3", record["depends"], record)

        # fix numba / numpy compatibility; numba added a run_constrained entry
        # for numpy as of version=0.54.0; numpy<1.21a0 is a conservative upper
        # bound that may not be strict enough for old versions of numba
        if (
            record_name == "numba"
            and record.get("timestamp", 0) <= 1671537177000
            and parse_version(record["version"]) < parse_version("0.54")
        ):
            deps = record["depends"]
            for i, dep in enumerate(deps):
                if dep == "numpy":
                    deps[i] = "numpy <1.21.0a0"
                    break
                if dep.startswith("numpy ") and "<" in dep:
                    _pin_stricter(fn, record, "numpy", "x.x", "1.21")
                    break
                if dep.startswith("numpy ") and ">" in dep:
                    deps[i] += ",<1.21.0a0"
                    break

        if record_name == "calliope":
            # Fix missing dependency in Calliope that is required by some methods in
            # xarray=2022.3, but is not a dependency in their recipe.
            # This was fixed in https://github.com/conda-forge/calliope-feedstock/pull/30
            # This patches build 0 with the right information too.
            if (
                record.get("timestamp", 0) <= 1673531497000
                and record["build_number"] == 0
                and parse_version(record["version"])
                == parse_version("0.6.9")
            ):
                record["depends"].append("bottleneck")

            # Pin libnetcdf upper bound due to breaking change in version >=4.9
            # This was fixed in https://github.com/conda-forge/calliope-feedstock/pull/32
            # This patches build 0 of latest release and all previous versions.
            if record.get("timestamp", 0) <= 1677053718000 and (
                parse_version(record["version"])
                < parse_version("0.6.10")
                or (
                    parse_version(record["version"])
                    == parse_version("0.6.10")
                    and record["build_number"] == 0
                )
            ):
                if "libnetcdf" in record["depends"]:
                    _replace_pin(
                        "libnetcdf", "libnetcdf <4.9", record["depends"], record
                    )

        # Dill dropped support for python <3.7 starting in version 0.3.5
        # Fixed in https://github.com/conda-forge/dill-feedstock/pull/35
        if record_name == "dill":
            pversion = parse_version(record["version"])
            zero_three_five = parse_version("0.3.5")
            zero_three_six = parse_version("0.3.6")

            if (pversion >= zero_three_five and pversion < zero_three_six) or (
                pversion == zero_three_six and record["build"].endswith("_0")
            ):
                _replace_pin("python >=3.5", "python >=3.7", record["depends"], record)

        # altair 4.2.0 and below are incompatible with jsonschema>=4.17 when certain
        # other packages are installed; this was fixed in
        # https://github.com/conda-forge/altair-feedstock/pull/41
        if (
            record_name == "altair"
            and parse_version(record["version"]).major == 4
            and record.get("timestamp", 0) <= 1673569551000
        ):

            if parse_version(record["version"]) < parse_version("4.2.0"):
                _replace_pin("jsonschema", "jsonschema <4.17", record["depends"], record)

            if parse_version(record["version"]) == parse_version("4.2.0"):
                _replace_pin("jsonschema >=3.0", "jsonschema >=3.0,<4.17", record["depends"], record)

                # this also applies the fix from https://github.com/conda-forge/altair-feedstock/pull/40
                _replace_pin("jsonschema", "jsonschema >=3.0,<4.17", record["depends"], record)

        # jsonschema 4.18.1 broke altair and many other packages
        # https://github.com/python-jsonschema/jsonschema/issues/1124
        if record_name == "altair" and record["version"] == "5.0.1" and record.get("timestamp", 0) < 1689170816000:
            _replace_pin("jsonschema >=3.0", "jsonschema >=3.0,!=4.18.1", deps, record)


        # isort dropped support for python 3.6 in version 5.11.0 and dropped support
        # for python 3.7 in version 5.12.0, but did not update the dependency in their recipe
        # Fixed in https://github.com/conda-forge/isort-feedstock/pull/78
        if record_name == "isort":
            pversion = parse_version(record["version"])
            five_eleven_zero = parse_version("5.11.0")
            five_twelve_zero = parse_version("5.12.0")
            if pversion >= five_eleven_zero and pversion < five_twelve_zero:
                _replace_pin("python >=3.6,<4.0", "python >=3.7,<4.0", record["depends"], record)
            elif pversion == five_twelve_zero:
                _replace_pin("python >=3.6,<4.0", "python >=3.8,<4.0", record["depends"], record)

        # sdt-python 17.5 needs Python >= 3.9 because of typing.Literal, but feedstock
        # specified >= 3.7
        # Fixed in https://github.com/conda-forge/sdt-python-feedstock/pull/20
        if (
            record_name == "sdt-python" and
            record["version"] == "17.5" and
            record["build_number"] == 0 and
            record.get("timestamp", 0) < 1676036991000
        ):
            _replace_pin("python >=3.7", "python >=3.9", record["depends"], record)

        # babel >=2.12 requires Python 3.7, but feedstock specified >= 3.6
        # Fixed in https://github.com/conda-forge/babel-feedstock/pull/26
        if (
            record_name == "babel" and
            record["version"] in {"2.12.0", "2.12.1"} and
            record["build_number"] == 0 and
            record.get("timestamp", 0) < 1677771669000
        ):
            _replace_pin("python >=3.6", "python >=3.7", record["depends"], record)

        # mamba >= 1.2.0 requires conda>=4.14.0, but feedstock specified >= 4.8
        # Fixed in https://github.com/conda-forge/mamba-feedstock/pull/175
        if (
            record_name == "mamba" and
            record["version"] in {"1.2.0", "1.3.0", "1.3.1"} and
            record.get("timestamp", 0) < 1678096271000
        ):
            _replace_pin("conda >=4.8,<23.4", "conda >=4.14,<23.4", record["depends"], record)

        # pyopenssl 22 used in combination with Cryptography 39 breaks with error
        # "AttributeError: module 'lib' has no attribute 'OpenSSL_add_all_algorithms'".
        # We must pin down cryptography to <39
        if (
            record_name == "pyopenssl" and
            record["version"] == "22.0.0" and
            record.get("timestamp", 0) < 1678096271000
        ):
            _replace_pin("cryptography >=35.0", "cryptography >=35.0,<39", record["depends"], record)

        if (
            record_name == "libtiff" and
            record["version"] == "4.5.0" and
            record["build_number"] == 3 and
            any(d.startswith("libjpeg-turbo")
                for d in record.get("depends", [])) and
            record.get("timestamp", 0) < 1678151067000
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("jpeg <0.0.0a")
            record["constrains"] = new_constrains

        if (
            record_name == "libwebp" and
            record["version"] == "1.2.4" and
            record["build_number"] == 2 and
            any(d.startswith("libjpeg-turbo")
                for d in record.get("depends", [])) and
            record.get("timestamp", 0) < 1678151067000
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("jpeg <0.0.0a")
            record["constrains"] = new_constrains

        if (
            record_name == "gst-plugins-good" and
            record["version"] == "1.22.0" and
            record["build_number"] == 1 and
            any(d.startswith("libjpeg-turbo")
                for d in record.get("depends", [])) and
            record.get("timestamp", 0) < 1678151067000
        ):
            new_constrains = record.get("constrains", [])
            new_constrains.append("jpeg <0.0.0a")
            record["constrains"] = new_constrains

        # cfn-lint has not been reliably updating the aws-sam-translator
        # dependency. This leads to lots of invalid environments involving older
        # packages when fsspec is involved, due to the behavior described in
        # <https://github.com/conda-forge/filesystem-spec-feedstock/issues/79>
        # Fixed going forward in:
        # <https://github.com/conda-forge/cfn-lint-feedstock/pull/177>
        if (
            record_name == "cfn-lint" and
            record.get("timestamp", 0) < 1692540625000
        ):
            correct_aws_sam_translator_dependencies = {
                "0.20.1": ">=1.10.0", "0.20.2": ">=1.10.0", "0.21.2": ">=1.10.0",
                "0.22.0": ">=1.12.0", "0.23.1": ">=1.13.0", "0.23.2": ">=1.13.0",
                "0.56.0": ">=1.40.0", "0.56.1": ">=1.40.0", "0.56.2": ">=1.40.0",
                "0.56.3": ">=1.42.0", "0.56.4": ">=1.42.0", "0.57.0": ">=1.42.0",
                "0.58.0": ">=1.42.0", "0.58.1": ">=1.42.0", "0.58.2": ">=1.42.0",
                "0.58.3": ">=1.42.0", "0.58.4": ">=1.42.0", "0.59.0": ">=1.45.0",
                "0.59.1": ">=1.45.0", "0.60.0": ">=1.45.0", "0.60.1": ">=1.45.0",
                "0.61.0": ">=1.45.0", "0.61.1": ">=1.46.0", "0.61.2": ">=1.46.0",
                "0.61.3": ">=1.47.0", "0.61.4": ">=1.48.0", "0.61.5": ">=1.49.0",
                "0.62.0": ">=1.50.0", "0.63.0": ">=1.50.0", "0.63.1": ">=1.50.0",
                "0.63.2": ">=1.50.0", "0.64.0": ">=1.50.0", "0.64.1": ">=1.50.0",
                "0.65.0": ">=1.50.0", "0.65.1": ">=1.51.0", "0.66.0": ">=1.51.0",
                "0.66.1": ">=1.51.0", "0.67.0": ">=1.52.0", "0.68.0": ">=1.53.0",
                "0.68.1": ">=1.53.0", "0.69.0": ">=1.53.0", "0.69.1": ">=1.53.0",
                "0.70.1": ">=1.53.0", "0.71.0": ">=1.53.0", "0.71.1": ">=1.54.0",
                "0.72.0": ">=1.54.0", "0.72.1": ">=1.54.0", "0.72.2": ">=1.55.0",
                "0.72.3": ">=1.55.0", "0.72.4": ">=1.55.0", "0.72.5": ">=1.55.0",
                "0.72.6": ">=1.55.0", "0.72.7": ">=1.56.0", "0.72.8": ">=1.56.0",
                "0.72.10": ">=1.57.0", "0.73.0": ">=1.59.0", "0.73.1": ">=1.59.0",
                "0.73.2": ">=1.59.0", "0.74.1": ">=1.60.1", "0.74.3": ">=1.60.1",
                "0.75.0": ">=1.60.1", "0.75.1": ">=1.60.1", "0.76.1": ">=1.62.0",
                "0.76.2": ">=1.62.0", "0.77.0": ">=1.64.0", "0.77.1": ">=1.64.0",
                "0.77.2": ">=1.64.0", "0.77.3": ">=1.64.0", "0.77.4": ">=1.65.0",
                "0.77.5": ">=1.65.0", "0.77.6": ">=1.68.0", "0.77.7": ">=1.68.0",
                "0.77.8": ">=1.68.0", "0.77.9": ">=1.68.0", "0.77.10": ">=1.68.0",
                "0.78.1": ">=1.70.0", "0.78.2": ">=1.71.0", "0.79.1": ">=1.71.0",
                "0.79.4": ">=1.71.0", "0.79.5": ">=1.71.0", "0.79.6": ">=1.71.0",
                "0.79.7": ">=1.71.0"
            }
            if record["version"] in correct_aws_sam_translator_dependencies:
                pin = correct_aws_sam_translator_dependencies[record["version"]]
                for n, dep in enumerate(record["depends"]):
                    if dep.startswith("aws-sam-translator "):
                        record["depends"][n] = f"aws-sam-translator {pin}"

        # fsspec ==2023.3.1 requires Python 3.8
        # Fixed in https://github.com/conda-forge/babel-feedstock/pull/26
        if (
            record_name == "fsspec" and
            record["version"] == "2023.3.0" and
            record["build_number"] == 0 and
            record.get("timestamp", 0) < 1678285727000
        ):
            _replace_pin("python >=3.6", "python >=3.8", record["depends"], record)

        # imath 3.1.7 change its SOVERSION so it is not not ABI compatible
        # with imath 3.1.4, 3.1.5, and 3.1.6
        # See https://github.com/conda-forge/imath-feedstock/issues/7
        if (
            has_dep(record, "imath") and
            record.get('timestamp', 0) < 1678196668497
        ):
            _pin_stricter(fn, record, "imath", "x", upper_bound="3.1.7")

        if (
            record_name == "openexr" and
            record["version"] == "3.1.5" and
            # build 2 was built after the repo data patch above went into place
            # but erroneously used an old version of imath without
            # the stricter pin
            record["build_number"] == 2 and
            record.get('timestamp', 0) < 1678332917000
        ):
            _pin_stricter(fn, record, "imath", "x", upper_bound="3.1.7")

        # cppyy <3 uses a version of Cling that is based on Clang 9. libcxx 15
        # headers for macOS do not compile with such an old Clang anymore, see
        # https://github.com/conda-forge/libcxx-feedstock/issues/111
        # So, if there's is no "<" pin on libcxx already, we add a "<15".
        if (
            record_name == "cppyy" and
            parse_version(record["version"]) < parse_version("3.0.0") and
            record.get("timestamp", 0) < 1678353800000
        ):
            depends = record.get("depends", [])
            for i, depend in enumerate(depends):
                if depend.split()[0] == "libcxx":
                    if "<" not in depend:
                        if " " not in depend:
                            depend += " "
                        else:
                            depend += ","
                        depend += "<15"
                    depends[i] = depend
            record["depends"] = depends

        # related to https://github.com/conda-forge/nvidia-apex-feedstock/issues/29
        if (
            record_name == "nvidia-apex" and
            any("=*=cuda|=*=gpu" in constr for constr in record.get("constrains", [""])) and
            record.get("timestamp", 0) < 1678454014000
        ):
            record["constrains"] = ["pytorch =*=cuda*", "nvidia-apex-proc =*=cuda"]

        # tensorly 0.8.0+ need python 3.8+
        # https://github.com/conda-forge/tensorly-feedstock/issues/12
        # Fixed in https://github.com/conda-forge/tensorly-feedstock/pull/14
        if (
            record_name == "tensorly" and
            (record["version"] == "0.8.0" or record["version"] == "0.8.1") and
            record["build_number"] == 0 and
            record.get("timestamp", 0) < 1678253357320
        ):
            _replace_pin("python >=3.6", "python >=3.8", record["depends"], record)

        # cmor <= 3.7.1 needs numpy <1.24
        # https://github.com/conda-forge/cmor-feedstock/issues/59
        # Fixed in https://github.com/conda-forge/cmor-feedstock/pull/60
        if (
            record_name == "cmor" and
            record.get("timestamp", 0) < 1679388583000
        ):
            pversion = parse_version(record["version"])
            v371 = parse_version("3.7.1")
            if (
                pversion < v371 or
                (pversion == v371 and record["build_number"] < 4)
            ):
                _pin_stricter(fn, record, "numpy", "x", upper_bound="1.24")

        # cuda-cccl and cuda-cccl-impl (released with CUDA 12) ship the same
        # files as existing thrust/cub packages. These should conflict.
        # Eventually users of thrust/cub should migrate to cuda-cccl[-impl]
        if record_name in {"thrust", "cub"}:
            new_constrains = record.get('constrains', [])
            new_constrains.append("cuda-cccl <0.0.0a0")
            new_constrains.append("cuda-cccl-impl <0.0.0a0")
            new_constrains.append(f"cuda-cccl_{subdir} <0.0.0a0")
            record['constrains'] = new_constrains

        # pystac >=1.6.0 dropped Python < 3.8. This only affects 1.6.0, >=1.6.0 were fixed already.
        # https://github.com/conda-forge/pystac-feedstock/issues/22
        if record_name == "pystac" and record["version"] == "1.6.0" and record.get("timestamp", 0) < 1681128912000:
            _replace_pin("python >=3.6", "python >=3.8", deps, record)

        if record.get('timestamp', 0) < 1681344601000:
            deps = record.get("depends", [])
            if any(dep.startswith(("libcurl", "curl")) and dep.endswith("<8.0a0") for dep in deps):
                _pin_looser(fn, record, "curl", upper_bound="9.0")
                _pin_looser(fn, record, "libcurl", upper_bound="9.0")

        # anndata 0.9.0 dropped support for Python 3.7 but build 0 didn't
        # update the Python pin. Fixed for build_number 1 in
        # https://github.com/conda-forge/anndata-feedstock/pull/28
        if (
            record_name == "anndata"
            and record["version"] == "0.9.0"
            and record["build_number"] == 0
            and record.get("timestamp", 0) < 1681324213000
           ):
            _replace_pin("python >=3.6", "python >=3.8", record["depends"], record)

        # emmet-core <=0.58.0 needs pydantic <2
        if (
            record_name == "emmet-core" and
            record["version"] < "0.58.0" or
            (
                record["version"] == "0.58.0" and
                record["build_number"] == 0
            )
        ):
            _replace_pin("pydantic >=1.10.2", "pydantic >=1.10.2,<2",
                         record["depends"], record)

        if (
            record_name == "emmet-core" and
            record["version"] == "0.58.0" and
            record["build_number"] == 2
        ):
            _replace_pin("pydantic >=2", "pydantic >=1.10.2,<2",
                         record["depends"], record)

        # scikit-image 0.20.0 needs scipy scipy >=1.8,<1.9.2 for python <= 3.9
        # Fixed in https://github.com/conda-forge/scikit-image-feedstock/pull/102
        if (
            record_name == "scikit-image" and
            record["version"] == "0.20.0" and
            record["build_number"] == 0 and
            record.get('timestamp', 0) < 1681732616000 and
            ('python >=3.8,<3.9.0a0' in record["depends"] or
             'python >=3.9,<3.10.0a0' in record["depends"])
        ):
            _replace_pin("scipy >=1.8", "scipy >=1.8,<1.9.2",
                         record["depends"], record)

        # intake-esm v2023.4.20 dropped support for Python 3.8 but build 0 didn't update
        # the Python version pin.
        if (
            record_name == "intake-esm"
            and record["version"] == "2023.4.20"
            and record["build_number"] == 0
            and record.get("timestamp", 0) < 1682227052000
        ):
            _replace_pin("python >=3.8", "python >=3.9", record["depends"], record)

        if (
            record_name == "sqlalchemy-cockroachdb" and
            record["version"] == "2.0.0" and
            record["build_number"] == 0 and
            record.get("timestamp", 0) <= 1680784303548
        ):
            _replace_pin("sqlalchemy <2.0.0", "sqlalchemy >=2.0.0", record["depends"], record)

        if (
            record_name == "libtensorlight" and
            record["version"] == "3.0.1" and
            record["build_number"] == 0 and
            record.get("timestamp", 0) <= 1682609291000
        ):
            record["depends"].append("libblas * *mkl")

        if (
            record_name == "etils" and
            record["version"].startswith("1.") and
            record.get("timestamp", 0) < 1683949458062
        ):
            _replace_pin("python >=3.7", "python >=3.8", record["depends"], record)

        # Connexion 2.X is not compatible with Flask 2.3+
        # https://github.com/spec-first/connexion/issues/1699#issuecomment-1524042812
        if (
            record_name == "connexion" and
            record["version"][0] == "2" and
            record.get("timestamp", 0) <= 1680300000000
        ):
            _replace_pin("flask >=1.0.4,<3", "flask >=1.0.4,<2.3", record["depends"], record)

        # attrs >=22.2.0 requires Python 3.6, and >=23.1.0 requires 3.7, but feedstock specified >= 3.5
        # Fixed in https://github.com/conda-forge/attrs-feedstock/pull/32
        if (
            record_name == "attrs"
            and record["version"] in {"22.2.0"}
            and record.get("timestamp", 0) < 1683636279000
        ):
            _replace_pin("python >=3.5", "python >=3.6", record["depends"], record)
        if (
            record_name == "attrs"
            and record["version"] in {"23.1.0"}
            and record["build_number"] == 0
            and record.get("timestamp", 0) < 1683636279000
        ):
            _replace_pin("python >=3.5", "python >=3.7", record["depends"], record)

        # connexion 2.14.2=0 has incorrect dependencies
        # fixed for 2.14.2=1 in https://github.com/conda-forge/connexion-feedstock/pull/35/files
        if (
            record_name == "connexion"
            and record["version"] in {"2.14.2"}
            and record["build_number"] == 0
            and record.get("timestamp", 0) < 1684322706000
        ):
            _replace_pin("python >=3.6", "python >=3.8", record["depends"], record)
            _replace_pin("werkzeug >=1.0,<3.0", "werkzeug >=1.0,<2.3", record["depends"], record)
            record["depends"].remove("importlib-metadata >=1")

        if record_name == "conda-content-trust" and record.get("timestamp", 0) < 1685589411000:  # 2023-06-01
            _replace_pin("cryptography", "cryptography <41.0.0a0", record["depends"], record)

        # skl2onnx requires onnx<1.15 for versions older than 1.14.1
        # see https://github.com/onnx/onnx/issues/5202
        if (
            record_name == "skl2onnx"
            and parse_version(record["version"]) < parse_version("1.14.1")
            and record.get("timestamp", 0) < 1686557425000
        ):
            _replace_pin("onnx >=1.2.1", "onnx >=1.2.1,<1.15", record["depends"], record)

        # noarch depfinder packages are broken for python >=3.10
        if (
            record_name == "depfinder"
            and record.get("timestamp", 0) < 1659704295850
            and subdir == "noarch"
            and any(
                "<" not in dep
                for dep in record.get("depends", [])
                if dep.startswith("python ")
            )
        ):
            pind = None
            for i, dep in enumerate(record.get("depends", [])):
                if dep.startswith("python "):
                    pind = i
                    break

            if pind is not None:
                record["depends"][pind] = record["depends"][pind] + ",<3.10"

        if record_name == "qcportal" and record.get("timestamp", 0) < 1691162578000:
            # QCPortal does not work with Pydantic 2, and no released version has.
            for dep in record.get("depends", []):
                if dep.split()[0] == "pydantic":
                    _replace_pin(dep, f"{dep},<2.0a0", record.get("depends", []), record)

        # apscheduler 3.8.1 through 3.10.1 has incorrect version restiction for tzlocal
        if (
            record_name == "apscheduler"
            and record.get("timestamp", 0) < 1689345788000
            and parse_version(record["version"]) >= parse_version("3.8.1")
            and parse_version(record["version"]) <= parse_version("3.10.1")
        ):
            _replace_pin("tzlocal >=2.0,<3.0", "tzlocal >=2.0,!=3.*", record["depends"], record)

        if (
            record_name == "zstandard"
            and record.get("timestamp", 0) < 1689939052321
            and record["version"] == "0.19.0"
            and record["build_number"] == 1
        ):
            _replace_pin("zstd >=1.5.2,<1.6.0a0", "zstd ==1.5.2", record["depends"], record)

        # jax 0.4.14 removes jax.ShapedArray, which is imported by flax<0.6.9
        if (
            record_name == "flax"
            and parse_version(record["version"]) < parse_version("0.6.9")
            and record.get("timestamp", 0) < 1692133728000
        ):
            _replace_pin("jax >=0.3.2", "jax >=0.3.2,<0.4.14", record["depends"], record)
            _replace_pin("jax >=0.2.6", "jax >=0.2.6,<0.4.14", record["depends"], record)

    return index


def _add_pybind11_abi_constraint(fn, record):
    """the pybind11-abi package uses the internals version

    here are the ranges

    v2.2.0 1
    v2.2.1 1
    v2.2.2 1
    v2.2.3 1
    v2.2.4 2
    v2.3.0 3
    v2.4.0 3
    v2.4.1 3
    v2.4.2 3
    v2.4.3 3
    v2.5.0 4
    v2.6.0 4
    v2.6.0b1 4
    v2.6.0rc1 4
    v2.6.0rc2 4
    v2.6.0rc3 4
    v2.6.1 4

    prior to 2.2.0 we set it to 0
    """
    ver = parse_version(record["version"])

    if ver < parse_version("2.2.0"):
        abi_ver = "0"
    elif ver < parse_version("2.2.4"):
        abi_ver = "1"
    elif ver < parse_version("2.3.0"):
        abi_ver = "2"
    elif ver < parse_version("2.5.0"):
        abi_ver = "3"
    elif ver <= parse_version("2.6.1"):
        abi_ver = "4"
    else:
        # past this we should have a constrains there already
        raise RuntimeError(
            "pybind11 version %s out of range for abi" % record["version"]
        )

    constrains = record.get("constrains", [])
    found_idx = None
    for idx in range(len(constrains)):
        if constrains[idx].startswith("pybind11-abi "):
            found_idx = idx

    if found_idx is None:
        constrains.append("pybind11-abi ==" + abi_ver)
    else:
        constrains[found_idx] = "pybind11-abi ==" + abi_ver

    record["constrains"] = constrains


def _fix_libgfortran(fn, record):
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == "libgfortran"),
        None
    )
    if dep_idx is not None:
        # make sure respect minimum versions still there
        # 'libgfortran'         -> >=3.0.1,<4.0.0.a0
        # 'libgfortran ==3.0.1' -> ==3.0.1
        # 'libgfortran >=3.0'   -> >=3.0,<4.0.0.a0
        # 'libgfortran >=3.0.1' -> >=3.0.1,<4.0.0.a0
        if ("==" in depends[dep_idx]) or ("<" in depends[dep_idx]):
            pass
        elif depends[dep_idx] == "libgfortran":
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record['depends'] = depends
        elif ">=3.0.1" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0.1,<4.0.0.a0"
            record['depends'] = depends
        elif ">=3.0" in depends[dep_idx]:
            depends[dep_idx] = "libgfortran >=3.0,<4.0.0.a0"
            record['depends'] = depends
        elif ">=4" in depends[dep_idx]:
            # catches all of 4.*
            depends[dep_idx] = "libgfortran >=4.0.0,<5.0.0.a0"
            record['depends'] = depends


def _set_osx_virt_min(fn, record, min_vers):
    rconst = record.get("constrains", ())
    dep_idx = next(
        (q for q, dep in enumerate(rconst)
         if dep.split(' ')[0] == "__osx"),
        None
    )
    run_constrained = list(rconst)
    if dep_idx is None:
        run_constrained.append("__osx >=%s" % min_vers)
    if run_constrained:
        record['constrains'] = run_constrained


def _fix_libcxx(fn, record):
    record_name = record["name"]
    if not record_name in ["cctools", "ld64", "llvm-lto-tapi"]:
        return
    depends = record.get("depends", ())
    dep_idx = next(
        (q for q, dep in enumerate(depends)
         if dep.split(' ')[0] == "libcxx"),
        None
    )
    if dep_idx is not None:
        dep_parts = depends[dep_idx].split(" ")
        if len(dep_parts) >= 2 and dep_parts[1] == "4.0.1":
            # catches all of 4.*
            depends[dep_idx] = "libcxx >=4.0.1"
            record['depends'] = depends


def _extract_and_remove_vc_feature(record):
    features = record.get('features', '').split()
    vc_features = tuple(f for f in features if f.startswith('vc'))
    if not vc_features:
        return None
    non_vc_features = tuple(f for f in features if f not in vc_features)
    vc_version = int(vc_features[0][2:])  # throw away all but the first
    if non_vc_features:
        record['features'] = ' '.join(non_vc_features)
    else:
        record['features'] = None
    return vc_version


def _do_subdir(subdir):
    repodata_url = "/".join(
        (CHANNEL_ALIAS, CHANNEL_NAME, subdir, "repodata_from_packages.json"))
    response = requests.get(repodata_url)
    response.raise_for_status()
    repodata = response.json()

    prefix_dir = os.getenv("PREFIX", "tmp")
    prefix_subdir = join(prefix_dir, subdir)
    if not isdir(prefix_subdir):
        os.makedirs(prefix_subdir)

    # Step 2a. Generate a new index.
    new_index = _gen_new_index(repodata, subdir)

    # Step 2b. Generate the instructions by diff'ing the indices.
    instructions = _gen_patch_instructions(repodata, new_index, subdir)

    # Step 2c. Output this to $PREFIX so that we bundle the JSON files.
    patch_instructions_path = join(
        prefix_subdir, "patch_instructions.json")
    with open(patch_instructions_path, 'w') as fh:
        json.dump(
            instructions, fh, indent=2,
            sort_keys=True, separators=(',', ': '))


def main():
    if "CF_SUBDIR" in os.environ:
        # For local debugging
        subdirs = os.environ["CF_SUBDIR"].split(";")
    else:
        subdirs = SUBDIRS

    with ProcessPoolExecutor(max_workers=None) as exc:
        futs = [
            exc.submit(_do_subdir, subdir)
            for subdir in subdirs
        ]
        for fut in tqdm.tqdm(futs, desc="patching repodata"):
            fut.result()


if __name__ == "__main__":
    sys.exit(main())
