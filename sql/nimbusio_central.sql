/****
 * schema for centralized nimbus.io database
 ****/

begin;

drop schema if exists nimbusio_central cascade;
create schema nimbusio_central;
set search_path to nimbusio_central, public;

/* just a mostly informational table to describe the details of the whole cluster */
create table "cluster" (
    id serial primary key,
    name varchar(255) unique not null,
    node_count int4 not null default 10,
    replication_level int4 not null default 3,
    creation_time timestamp default 'now'
);

create table node (
    id serial primary key,
    cluster_id int4 not null,
    node_number_in_cluster int4 not null,
    name varchar(255) unique not null,
    hostname varchar(255) not null,
    offline bool not null default false,
    creation_time timestamp default 'now'
);

create sequence customer_id_seq;
create table customer (
    id int4 primary key default nextval('nimbusio_central.customer_id_seq'),
    username varchar(60) unique not null,
    creation_time timestamp not null default now(),
    deletion_time timestamp
);

create sequence customer_key_id_seq;
create table customer_key(
   id int4 unique not null default nextval('nimbusio_central.customer_key_id_seq'),  
   customer_id int4 not null references nimbusio_central.customer(id),
   key text unique not null,
   description text,
   creation_time timestamp not null default now(),
   deletion_time timestamp
);

create index customer_key_customer_idx on nimbusio_central.customer_key("customer_id");

create sequence collection_id_seq;
create table collection (
    id int4 primary key default nextval('nimbusio_central.collection_id_seq'),
    name varchar(63) unique not null,
    customer_id int4 not null references nimbusio_central.customer(id),
    cluster_id int4 not null references nimbusio_central.cluster(id),
    versioning bool not null default false,
    access_control text,
    creation_time timestamp not null default 'now',
    deletion_time timestamp
);


/* get all collection names for customer_id */
create index collection_customer_id_name_idx on nimbusio_central.collection("customer_id", "name");

create table space_accounting(
   collection_id int4 not null references nimbusio_central.collection(id),
   timestamp timestamp not null,
   bytes_added int8 not null default 0,
   bytes_removed int8 not null default 0,
   bytes_retrieved int8 not null default 0
);

/* rollback; */
commit;

