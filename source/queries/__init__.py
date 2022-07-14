__all__ = ('create', 'fetch', 'update', 'notify', 'initialize_database', 'update')

from . import update

_magic_hex = "X'80045D942E'"  # pickled empty list

create = f"""
    insert into posts values (:message_id, :channel_id, :activity, :author_id, :unix_time, {_magic_hex}, {_magic_hex})
"""
fetch = """
    select channel_id, activity, author_id, unix_time, main, reserve from posts where message_id = :message_id\
"""
delete = """
    delete from posts where message_id = :message_id 
"""
notify = """
    select message_id from posts where unix_time = :unix_time
"""
initialize_database = """
    create table posts
    (
        message_id integer not null
            constraint posts_pk
                primary key,
        channel_id integer not null,
        activity   text    not null,
        author_id  integer not null,
        unix_time  integer not null,
        main       blob,
        reserve    blob
    );

    create unique index posts_message_id_uindex
        on posts (message_id);
"""
