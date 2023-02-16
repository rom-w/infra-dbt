import psycopg2

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    database="testdb",
    user="postgres",
    password="Datorama01"
)

def get_or_assign_shards(model_id, prim_id, second_id):
    with conn.cursor() as c:
        c.execute("select * from sharding where model_id = %s", (model_id,))
        row = c.fetchone()
        if row:
            return row[1:]

        c.execute("insert into sharding(model_id,primary_shard_id,secondary_shard_id) values(%s,%s,%s)", (model_id, prim_id, second_id))
        conn.commit()
        return [prim_id, None, second_id, None]
