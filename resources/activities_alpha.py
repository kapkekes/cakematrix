from enum import StrEnum
from typing import Dict, NamedTuple

from discord import OptionChoice


class Activities(StrEnum):
    last_wish = 'lw'
    garden = 'gos'
    deep_stone = 'dsc'
    vault = 'vog'
    vault_master = 'vog-master'
    vow = 'votd'
    vow_master = 'votd-master'


class Profile(NamedTuple):
    name: str
    power: int
    thumbnail_url: str


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

option_choices = [OptionChoice(information.name, value) for value, information in profiles_new.items()]
