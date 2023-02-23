import compile_sql
from locust import task, User, between, clients

import locust
import random

import time

# /Users/afinkelstein/work/infra-dbt/test_dbt 0 0 5

# project_dir = "/Users/afinkelstein/work/infra-dbt/test_dbt"

model_path = "s3test/modeldump.json"

SERVER_HOST_COMPILE = "http://0.0.0.0:8585/compile"

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

class CompileTask(User):
    wait_time = between(0.1, 0.5)

    def __init__(self, environment):
        super().__init__(environment)
        self.environment = environment

        self.clients = [
            clients.HttpSession(
                base_url="http://0.0.0.0:858%d" % i,
                request_event=self.environment.events.request,
                user=self
                # pool_manager=self.pool_manager,
            )
            for i in range(3)
        ]

    @task
    def compile_task(self):
        state_id = random.randint(0, 10)

        json={"state_id": str(state_id), "sql": sql, "model_version":0, "model_loc": model_path}
        self.clients[state_id % 3].post("/compile_fetch", json=json)
