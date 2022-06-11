create table lfg_posts
(
    response_id      integer not null
        constraint table_name_pk
            primary key,
    activity         text    not null,
    author_id        integer not null,
    timestamp        text    not null,
    main             blob,
    reserve          blob
);

create unique index table_name_response_id_uindex
    on lfg_posts (response_id);