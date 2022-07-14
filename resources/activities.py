from typing import Dict, NamedTuple

from discord import OptionChoice


class Profile(NamedTuple):
    name: str
    power: int
    thumbnail_url: str


profiles: Dict[str, Profile] = {
    'lw': Profile(
        'Последнее желание', 1350,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/last-wish.jpg'
    ),
    'gos': Profile(
        'Сад спасения', 1350,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/garden-of-salvation.jpg'
    ),
    'dsc': Profile(
        'Склеп Глубокого камня', 1350,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/deep-stone-crypt.jpg'
    ),
    'vog': Profile(
        'Хрустальный чертог', 1350,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vault-of-glass.jpg'
    ),
    'vog-master': Profile(
        'Хрустальный чертог (мастер)', 1590,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vault-of-glass.jpg'
    ),
    'votd': Profile(
        'Клятва послушника', 1550,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vow-of-the-disciple.jpg'
    ),
    'votd-master': Profile(
        'Клятва послушника (мастер)', 1590,
        'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vow-of-the-disciple.jpg'
    )
}

option_choices = [OptionChoice(information.name, value) for value, information in profiles.items()]
