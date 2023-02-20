import sys
import hashlib
import os
import requests
import json
import queue

import model_utils
import sharding_client
import threading

SERVER_HOST_PUSH = "http://0.0.0.0:%d/push"
SERVER_HOST_PARSE = "http://0.0.0.0:%d/parse"
SERVER_HOST_COMPILE = "http://0.0.0.0:%d/compile"


def call_compile(project_dir, model_version, shards_order, model_id=None):
    if model_id is None:
        model_id = hashlib.md5(os.path.abspath(project_dir).encode()).hexdigest()

    print("model_id = %s, version = %d" % (model_id, model_version))

    model = sharding_client.get_or_assign_shards(model_id, shards_order)
    print("identified shards and versions", model)

    good_shards_q = queue.Queue()

    for shard in model.shards:
        if shard.version and shard.version == model_version:
            good_shards_q.put(shard.shard_id)
        else:
            threading.Thread(target=update_shard, args=(
            shard.shard_id, shard.order, good_shards_q, model.model_id, project_dir, model_version)).start()

    print("waiting for a ready shard...")
    good_shard_id = good_shards_q.get(block=True, timeout=60)
    print("shard %d is ready, compiling" % good_shard_id)

    shard_port = good_shard_id + 8580

    sql = """
    select *
    from {{ metrics.calculate(
            metric('test_update'),
            grain='week',
            dimensions=['name'],
            secondary_calculations=[
                metrics.rolling(aggregate="min", interval=4)
            ]) 
        }}
    """

    resp = requests.post(SERVER_HOST_COMPILE % shard_port, json={"state_id": model_id, "sql": sql, "target": "dev"})
    print("sql: ", json.loads(resp.content)['res']['compiled_code'])


def update_shard(shard_id, order, q, model_id, project_dir, model_version):
    shard_port = 8580 + shard_id

    state = model_utils.get_state(project_dir)

    req = requests.post(SERVER_HOST_PUSH % shard_port, json={"state_id": model_id, "body": state})
    if req.status_code != 200:
        return

    req = requests.post(SERVER_HOST_PARSE % shard_port, json={"state_id": model_id})
    if req.status_code != 200:
        print("could not parse shard", shard_id)
        return

    sharding_client.update_shard_version(model_id, shard_id, model_version, order)

    q.put(shard_id)


if __name__ == "__main__":
    project_dir = sys.argv[1]
    model_version = int(sys.argv[2])
    shards_order = [int(v) for v in sys.argv[3].split(",")]

    call_compile(project_dir, model_version, shards_order)
