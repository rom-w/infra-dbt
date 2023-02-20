import psycopg2

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    database="testdb",
    user="postgres",
    password="Datorama01"
)


def get_or_assign_shards(model_id, shards_map):
    model = Model(model_id)

    with conn.cursor() as c:
        c.execute("select * from sharding where model_id = %s", (model_id,))
        rows = c.fetchall()
        if rows:
            for row in rows:
                model.add_shard(Shard(row[1], row[2], row[3]))
            return model

        for shard_id, shard_order in shards_map.items():
            c.execute("insert into sharding(model_id,shard_id,shard_primary_order) values(%s,%s,%s)",
                      (model_id, shard_id, shard_order))
            model.add_shard(Shard(shard_id, shard_order, None))
        conn.commit()

        return model


def update_shard_version(model_id, shard_id, model_version, order):
    with conn.cursor() as c:
        c.execute("update sharding "
                  "set shard_primary_order = %s, model_version = %s "
                  "where model_id = %s and shard_id = %s"
                  , (order, model_version, model_id, shard_id))
        conn.commit()


class Model:
    shards = []

    def __init__(self, model_id):
        self.model_id = model_id

    def __str__(self):
        listToStr = ' '.join(map(str, self.shards))
        return f"model_id = {self.model_id}, shards= [{listToStr}]"

    def add_shard(self, shard):
        self.shards.append(shard)


class Shard:
    def __init__(self, shard_id, order, version):
        self.shard_id = shard_id
        self.order = order
        self.version = version

    def __str__(self):
        return f"(shard_id = {self.shard_id}, order= {self.order}, version= {self.version})"
