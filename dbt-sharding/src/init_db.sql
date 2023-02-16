CREATE TABLE public.sharding (
                                 model_id varchar NOT NULL,
                                 primary_shard_id int4 NULL,
                                 primary_version int4 NULL,
                                 secondary_shard_id int4 NULL,
                                 secondary_version int4 NULL,
                                 CONSTRAINT newtable_pk PRIMARY KEY (model_id)
);