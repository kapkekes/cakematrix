from enum import StrEnum
from typing import Dict, NamedTuple

from discord import OptionChoice


class Profile(NamedTuple):
    name: str
    power: int
    thumbnail_url: str


class Activities(StrEnum):
    # raids

    last_wish = 'lw'             # the Last Wish
    garden = 'gos'               # the Garden of Salvation
    deep_stone = 'dsc'           # the Deep Stone Crypt
    vault = 'vog'                # the Vault of Glass
    vault_master = 'vog-master'  # the Vault of Glass, master difficulty
    vow = 'votd'                 # the Vow of the Disciple
    vow_master = 'votd-master'   # the Vow of the Disciple, master difficulty


profiles: Dict[Activities, Profile] = {
    Activities.last_wish: Profile(
        'Последнее желание',
        1350,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/last-wish.jpg'
    ),
    Activities.garden: Profile(
        'Сад спасения',
        1350,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/garden-of-salvation.jpg'
    ),
    Activities.deep_stone: Profile(
        'Склеп Глубокого камня',
        1350,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/deep-stone-crypt.png'
    ),
    Activities.vault: Profile(
        'Хрустальный чертог',
        1350,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vault-of-glass.jpg'
    ),
    Activities.vault_master: Profile(
        'Хрустальный чертог (мастер)',
        1590,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vault-of-glass.jpg'
    ),
    Activities.vow: Profile(
        'Клятва послушника',
        1550,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vow-of-the-disciple.png'
    ),
    Activities.vow_master: Profile(
        'Клятва послушника (мастер)',
        1590,
        'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vow-of-the-disciple.png'
    )
}

option_choices = [OptionChoice(information.name, value) for value, information in profiles.items()]
