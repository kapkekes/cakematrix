from typing import Dict

from discord import OptionChoice


profiles: Dict[str, Dict] = {
    'lw': {
        'name': 'Последнее желание',
        'power': 1350,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/last-wish.jpg'
    },
    'gos': {
        'name': 'Сад спасения',
        'power': 1350,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/garden-of-salvation.jpg'
    },
    'dsc': {
        'name': 'Склеп Глубокого камня',
        'power': 1350,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/deep-stone-crypt.jpg'
    },
    'vog': {
        'name': 'Хрустальный чертог',
        'power': 1350,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vault-of-glass.jpg'
    },
    'vog-master': {
        'name': 'Хрустальный чертог (мастер)',
        'power': 1590,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vault-of-glass.jpg'
    },
    'votd': {
        'name': 'Клятва послушника',
        'power': 1550,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vow-of-the-disciple.jpg'
    },
    'votd-master': {
        'name': 'Клятва послушника (мастер)',
        'power': 1590,
        'thumbnail':
            'https://raw.githubusercontent.com/kapkekes/cakematrix/main/resources/thumbnails/vow-of-the-disciple.jpg'
    }
}

optionChoices = [OptionChoice(information['name'], value) for value, information in profiles.items()]
