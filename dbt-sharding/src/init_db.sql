CREATE TABLE public.sharding (
                                 model_id varchar NOT NULL,
                                 shard_id int4 NULL,
                                 shard_primary_order int4 NULL,
                                 model_version int4 NULL,
                                 CONSTRAINT newtable_pk PRIMARY KEY (model_id, shard_id)
);