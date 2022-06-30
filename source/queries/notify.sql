select
    response_id, author_id, main, reserve
from
    lfg_posts
where
    timestamp = ?