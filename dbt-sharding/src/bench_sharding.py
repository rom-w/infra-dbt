import compile_sql
from locust import task, User, between
import random

import time

# /Users/afinkelstein/work/infra-dbt/test_dbt 0 0 5

project_dir = "/Users/lbuanos/work/infra-dbt/test_dbt"


class CompileTask(User):
    wait_time = between(0.1, 0.5)

    def __init__(self, environment):
        super().__init__(environment)
        self.environment = environment

    @task
    def compile_task(self):
        shard = random.randint(0, 2)

        start_perf_counter = time.perf_counter()
        start_time = time.time()

        model_id = str(random.randint(0, 10))

        compile_sql.call_compile(project_dir, 0, [shard, (shard + 1) % 3], model_id)

        self.environment.events.request.fire(
            request_type="ENQUEUE",
            name= str(model_id),
            start_time=start_time,
            response_time=(time.perf_counter() - start_perf_counter) * 1000,
            response_length=0,
            context={},
            exception=None,
        )