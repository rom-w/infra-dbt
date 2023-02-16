import os
import re
import yaml
import hashlib

VALID_FILE_EXTENSIONS = re.compile(r"^.+\.(sql|yml|yaml|md|csv|py|dbtignore)$")

PROJECT_PATH_KEYS = {
    "model-paths": {
        "default": ["models"],
        "aliases": ["source-paths"],
    },
    "analysis-paths": {
        "default": ["analyses"],
        "aliases": [],
    },
    "test-paths": {
        "default": ["tests"],
        "aliases": [],
    },
    "seed-paths": {
        "default": ["seeds"],
        "aliases": ["data-paths"],
    },
    "macro-paths": {
        "default": ["macros"],
        "aliases": [],
    },
    "snapshot-paths": {
        "default": ["snapshots"],
        "aliases": [],
    },
}

PACKAGE_PATH_KEY = "packages-install-path"
PACKAGE_PATH_DEFAULT = "dbt_packages"

def get_state(project_dir):
    dirs = get_all_project_paths(project_dir)
    return read_project(project_dir, dirs)

def get_all_project_paths(project_dir):
    project_paths = []
    packages_yml_path = get_packages_yml_path(project_dir)
    selectors_yml_path = get_selectors_yml_path(project_dir)
    if packages_yml_path is not None:
        project_paths.append(packages_yml_path)
    if selectors_yml_path is not None:
        project_paths.append(selectors_yml_path)
    project_root_paths = [project_dir] + get_package_dirs(project_dir)

    for project in project_root_paths:
        project_paths += get_project_paths(project)
    return project_paths

def get_packages_yml_path(project_dir):
    dbt_packages_yml_path = os.path.join(project_dir, "packages.yml")
    if not os.path.exists(dbt_packages_yml_path):
        return None
    return dbt_packages_yml_path

def read_project(project_dir, paths):
    manifest = {}
    for path in paths:
        for file in walk(path):
            relpath = os.path.relpath(file, project_dir)
            if is_syncable_file(relpath):
                file_contents = load(file)
                if file_contents is not None:
                    manifest[relpath] = file_contents
    return manifest

def is_syncable_file(path):
    return re.match(VALID_FILE_EXTENSIONS, path) is not None

def walk(root_dir):
    if os.path.isfile(root_dir):
        yield root_dir
        return

    for root, _, files in os.walk(root_dir):
        for name in files:
            path = os.path.join(root, name)
            if os.path.isdir(path):
                yield from walk(path)
            else:
                yield path

def get_project_paths(project_dir):
    """
    Returns all paths referenced from a dbt_project.yml file
    """
    dbt_project_yml_path = get_projects_yml_path(project_dir)
    dbtignore_path = os.path.join(project_dir, ".dbtignore")
    project_config = get_project_config(dbt_project_yml_path)

    all_paths = [dbt_project_yml_path, dbtignore_path]
    for key, key_info in PROJECT_PATH_KEYS.items():
        candidate_keys = [key] + key_info["aliases"]
        default = key_info.get("default", [])
        config_value = resolve_project_path_key(project_config, candidate_keys, default)
        all_paths += config_value

    # Relative to project dir
    return [os.path.join(project_dir, path) for path in all_paths]

def resolve_project_path_key(project_config, candidate_keys, default):
    NotFound = object()
    for key in candidate_keys:
        config_value = project_config.get(key, NotFound)
        if config_value is NotFound:
            continue
        elif isinstance(config_value, str):
            return [config_value]
        elif isinstance(config_value, (tuple, list)):
            return list(config_value)
        else:
            raise RuntimeError(
                f"Key {key} in dbt_project.yml file is not" "a list or string"
            )
    return default

def get_projects_yml_path(project_dir):
    dbt_project_yml_path = os.path.join(project_dir, "dbt_project.yml")
    if not os.path.exists(dbt_project_yml_path):
        raise Exception(
            f"dbt_project.yml file not found at {project_dir}."
            " Is this a valid dbt project?"
        )
    return dbt_project_yml_path

def get_selectors_yml_path(project_dir):
    selectors_yml_path = os.path.join(project_dir, "selectors.yml")
    if not os.path.exists(selectors_yml_path):
        return None
    return selectors_yml_path

def get_package_dirs(project_dir):
    package_dir_paths = []
    package_path = get_package_install_root_path(project_dir)
    root_dir = os.path.join(project_dir, package_path)

    if not os.path.exists(root_dir):
        return package_dir_paths

    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if os.path.isdir(path):
            package_dir_paths.append(path)
    return package_dir_paths


def get_package_install_root_path(project_dir):
    dbt_project_yml_path = get_projects_yml_path(project_dir)
    project_config = get_project_config(dbt_project_yml_path)
    return project_config.get(PACKAGE_PATH_KEY, PACKAGE_PATH_DEFAULT)

def get_project_config(dbt_project_yml_path):
    with open(dbt_project_yml_path) as fh:
        project_code = fh.read()
    return yaml.safe_load(project_code)

def load(filepath):
    with open(filepath, "rb") as fh:
        contents = fh.read()
        try:
            decoded_contents = contents.decode("utf-8")
        except UnicodeDecodeError:
            return None

        return {
            "contents": decoded_contents,
            "hash": hashlib.md5(contents).hexdigest(),
            "path": filepath,
        }