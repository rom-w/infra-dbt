import psycopg2

from psycopg2 import pool

postgreSQL_pool = pool.SimpleConnectionPool(1, 20, user="postgres",
                                                     password="Datorama01",
                                                     host="127.0.0.1",
                                                     port="5432",
                                                     database="testdb")


def get_or_assign_shards(model_id, shards_order):
    model = Model(model_id)

    with postgreSQL_pool.getconn() as conn:
        try:
            with conn.cursor() as c:
                c.execute("select * from sharding where model_id = %s", (model_id,))
                rows = c.fetchall()
                if rows:
                    for row in rows:
                        model.add_shard(Shard(row[1], row[2], row[3]))
                    return model

                for shard_order, shard_id in enumerate(shards_order):
                    c.execute("insert into sharding(model_id,shard_id,shard_primary_order) values(%s,%s,%s)",
                              (model_id, shard_id, shard_order))
                    model.add_shard(Shard(shard_id, shard_order, None))
                conn.commit()

                return model
        finally:
            postgreSQL_pool.putconn(conn)


def update_shard_version(model_id, shard_id, model_version, order):
    with postgreSQL_pool.getconn() as conn:
        try:
            with conn.cursor() as c:
                c.execute("update sharding "
                          "set shard_primary_order = %s, model_version = %s "
                          "where model_id = %s and shard_id = %s"
                          , (order, model_version, model_id, shard_id))
                conn.commit()
        finally:
            postgreSQL_pool.putconn(conn)

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
