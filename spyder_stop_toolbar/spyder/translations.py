# -*- coding: utf-8 -*-
"""Fonction de traduction du greffon.

`spyder.api.translations.get_translation("spyder_stop_toolbar")` marcherait aussi, mais tant
qu'aucun catalogue .mo n'est fourni elle affiche a chaque import un avertissement "No translation
file found for domain: ..." - du bruit dans la console a chaque demarrage.

Les libelles sont ecrits directement en francais, la langue de cette installation. On garde
l'habillage `_(...)`, qui permettra d'ajouter un catalogue plus tard sans toucher au reste du code,
mais sans en promettre un aujourd'hui.
"""


def _(message):
    return message
