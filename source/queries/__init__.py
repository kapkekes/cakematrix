__all__ = ('create_post', 'fetch_post', 'update')

from queries import update

_magic_hex = "X'80045D942E'"  # pickled empty list

create_post = f"""
    insert into posts values (:message_id, :channel_id, :activity, :author_id, :unix_time, {_magic_hex}, {_magic_hex})
"""
fetch_post = "select channel_id, author_id, unix_time, main, reserve from posts where message_id = :message_id"