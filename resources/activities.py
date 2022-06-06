from discord import OptionChoice


profiles = {
    'lw': {
        'name': 'Последнее желание',
        'power': 1350,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/last-wish.jpg'
    },
    'gos': {
        'name': 'Сад спасения',
        'power': 1350,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/garden-of-salvation.jpg'
    },
    'dsc': {
        'name': 'Склеп Глубокого камня',
        'power': 1350,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/deep-stone-crypt.png'
    },
    'vog': {
        'name': 'Хрустальный чертог',
        'power': 1350,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vault-of-glass.jpg'
    },
    'vog-master': {
        'name': 'Хрустальный чертог (мастер)',
        'power': 1590,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vault-of-glass.jpg'
    },
    'votd': {
        'name': 'Клятва послушника',
        'power': 1550,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vow-of-the-disciple.png'
    },
    'votd-master': {
        'name': 'Клятва послушника (мастер)',
        'power': 1590,
        'thumbnail': 'https://github.com/kapkekes/cake-o-matrix/raw/main/resources/thumbnails/vow-of-the-disciple.png'
    }
}

optionChoices = [OptionChoice(information['name'], value) for value, information in profiles.items()]
