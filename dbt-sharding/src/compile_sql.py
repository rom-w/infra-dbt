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

project_dir = sys.argv[1]
model_version = int(sys.argv[2])

prim_shard = int(sys.argv[3])
sec_shard = int(sys.argv[4])

model_id = hashlib.md5(os.path.abspath(project_dir).encode()).hexdigest()


def update_shard(shard_id, is_primary, q):
    shard_port = 8580 + shard_id

    state = model_utils.get_state(project_dir)

    req = requests.post(SERVER_HOST_PUSH % shard_port, json={"state_id": model_id, "body": state})
    if req.status_code != 200:
        return
    # # #
    # # # # POST /parse
    req = requests.post(SERVER_HOST_PARSE % shard_port, json={"state_id": model_id})
    if req.status_code != 200:
        print("could not parse shard",shard_id)
        return

    sharding_client.update_shard_version(model_id, model_version, is_primary)

    q.put(shard_id)


print("model_id = %s, version = %d" % (model_id, model_version))

shard1, ver1, shard2, ver2 = sharding_client.get_or_assign_shards(model_id, prim_shard, sec_shard)

print("identified shards and versions", shard1, ver1, shard2, ver2)

shard1_good = ver1 and ver1 == model_version
shard2_good = ver2 and ver2 == model_version

good_shards_q = queue.Queue()

if shard1_good:
    good_shards_q.put(shard1)
else:
    threading.Thread(target = update_shard, args = (shard1, True, good_shards_q)).start()
if shard2_good:
    good_shards_q.put()
else:
    threading.Thread(target = update_shard, args = (shard2, False, good_shards_q)).start()

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