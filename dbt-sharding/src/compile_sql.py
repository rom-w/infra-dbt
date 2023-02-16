import sys
import hashlib
import os
import requests
import json

import model_utils
import sharding_client

SERVER_HOST_PUSH = "http://0.0.0.0:8585/push"
SERVER_HOST_PARSE = "http://0.0.0.0:8585/parse"
SERVER_HOST_COMPILE = "http://0.0.0.0:8585/compile"
SERVER_HOST_MEM = "http://0.0.0.0:8585/"

project_dir = sys.argv[1]

model_id = hashlib.md5(os.path.abspath(project_dir).encode()).hexdigest()

print("model_id =", model_id)

print(sharding_client.get_or_assign_shards(model_id, 1, 2))

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

state = model_utils.get_state(project_dir)

req = requests.post(SERVER_HOST_PUSH, json={"state_id": model_id, "body": state})
print("PUSH", req.status_code)
# # #
# # # # POST /parse
req = requests.post(SERVER_HOST_PARSE, json={"state_id": model_id})
print("PARSE", req.status_code)

resp = requests.post(SERVER_HOST_COMPILE, json={"state_id": model_id, "sql": sql, "target": "dev"})
print("sql: ", json.loads(resp.content)['res']['compiled_code'])