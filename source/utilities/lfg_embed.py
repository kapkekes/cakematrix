from discord import Embed

from builders import numbered_list


class LFGEmbed(Embed):
    def __init__(self, response_id: int, activity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ...

    def rewrite_main(self, new):
        self._fields[1].value = numbered_list(new)

    def rewrite_reserve(self, new):
        self._fields[2].value = numbered_list(new)