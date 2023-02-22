import os
import shutil
from dbt_server.logging import GLOBAL_LOGGER as logger
from dbt_server.exceptions import StateNotFoundException

import boto3

s = boto3.Session(
    "ASIAXQLOLDSBVTQFXN2B",
    "CgN7GRiXTzL4Pf5gvtUBZ9K5y9O0XhpH0dPKUVyh",
    "IQoJb3JpZ2luX2VjEAEaCXVzLWVhc3QtMSJGMEQCIDG1GuF9+bbrNS/W7r9YxpTDvGS9tfJ7anSl2yl5fs/EAiAYPT6eOIJDapasb70gXAM6k7YC9onUhohMNIlthYU0jiqrAwiK//////////8BEAAaDDUxNjE2NDM2MTM0NyIMGuEtF+ndBAEwwlOnKv8CnZ7NigjoMeeqQCnqOwa3w5i4iLzEUoVGVHxre0Zo4gW/+Wg8yQjYqh/3v2gi5w4SnDlH2rypWZQMGukboDw2ENJ+sQtOWYw9CQG/q15/VsEGLGnUpbAqYFdeHof8TUkeX1VFtWvbuTYMafDF0h7lJRBpC1IS8+MHnqV+CAKSc4+K9Y/pSUq0EgsZA3GIfHNQwbpWSH8NBEOSC1a4bkFQ9AauJaDTI9w6/wmrGL8nb1lLiZ5oZCbx/T56Usg/P5d7u5c1BJgJBaI9yZDByG54fVqfvNhB8yQxuZ1D43WEANMQs5B/QDqwF1B+WmPA4ZnvbJC9r0dS++2c7HsVSTw335/ZIamzIy1EmJD4Me3QIjy16yFTreSX7jnZzFBtOeiHcIjOy94yYE4iqORezQSZZAvSifSojgK/oV+UVMLwfORht/RhfKNvkL68cg2k3J14obT0vu68M4F4efeSVs7r2HyQwZswDDrSI7t5RIHygAk6d5kP6RjBl8ei8uZBuj8w/+eSnwY64QGkI6l0vb1MO1lNz5Ham/SyiHXB04HIfQKPS6QhLO2lDf39mGHM494SZ/TV0nMaDDpeaKbaHPcvi2qzkEU4ul5MX7Hsp8ZW2K41ce7qSufKl4jRHUorkNT/KUGoI+6Gq5Idfgc55NYsUOrFZ+0Y82ZtBIfkDM1ug0047USSA23fmgKv/037Bwhg1eG+0OJh8ceiMs1j+Xs3FUPqIY+20BiSweOkninj+WJRFzwAvC1emzAJL6pqtdT2T0APNnF1A9VdswpdB5Imu0XZp8MJDz4MJzsYvXk+5fD4zbL1+d+8Z6U="
)

s3 = s.resource('s3')

s3client = s.client('s3');

bucket = 'dataagg-storage-datorama-dev1-uswest2-cdp001'


def get_working_dir():
    return os.environ.get("__DBT_WORKING_DIR", "s3test")


def get_root_path(state_id):
    working_dir = get_working_dir()
    return os.path.join(working_dir, f"state-{state_id}")


def get_latest_state_file_path():
    working_dir = get_working_dir()
    return os.path.join(working_dir, "latest-state-id.txt")


def get_path(state_id, *path_parts):
    return os.path.join(get_root_path(state_id), *path_parts)


def get_size(path):
    object = s3.Object(bucket, path)
    return object.get()['ContentLength']


def write_file(path, contents):
    if isinstance(contents, str):
        contents = contents.encode("utf-8")
    object = s3.Object(bucket, path)

    result = object.put(Body=contents)

def read_serialized_manifest(path):
    obj = s3.Object(bucket, path)
    return obj.get()['Body'].read().decode('utf-8')


def write_unparsed_manifest_to_disk(state_id, filedict):
    for filename, file_info in filedict.items():
        path = get_path(state_id, filename)
        write_file(path, file_info.contents)


def get_latest_state_id(state_id):
    if not state_id:
        path = os.path.abspath(get_latest_state_file_path())
        if not os.path.exists(path):
            logger.error("No state id included in request, no previous state id found.")
            return None
        with open(path, "r") as latest_path_file:
            state_id = latest_path_file.read().strip()
    return state_id


def update_state_id(state_id):
    path = os.path.abspath(get_latest_state_file_path())
    with open(path, "w+") as latest_path_file:
        latest_path_file.write(state_id)


def path_exists_s3(path):
    # obj = s3.Object(bucket, path)
    try:
        s3client.head_object(Bucket=bucket, Key=path)
        return True
    except:
        return False