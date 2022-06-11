select
    author_id, main_fireteam, reserve_fireteam
from
    lfg_posts
where
    response_id = ?