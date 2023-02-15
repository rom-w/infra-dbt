# main.py
import uvicorn

from dbt.tracking import do_not_track
from dbt.config import project
from dbt.config import selectors

import dbt_server.services.filesystem_service

do_not_track()

def load_from_s3(path):
    return dbt_server.services.filesystem_service.read_serialized_manifest(path)

old_path_exists = project.path_exists

def path_exists_s3(path):
    if "site-packages" in path:
        return old_path_exists(path)
    return dbt_server.services.filesystem_service.path_exists_s3(path)

#
# project.load_file_contents = load_from_s3
# project.path_exists = path_exists_s3
# selectors.path_exists = path_exists_s3


if __name__ == "__main__":
    uvicorn.run("dbt_server.views:app", port=8585, log_level="info", host="0.0.0.0")