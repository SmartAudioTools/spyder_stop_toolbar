# -*- coding: utf-8 -*-
"""Configuration du greffon "Barre Stop".

⚠ NE JAMAIS laisser le dictionnaire d'options VIDE. Un greffon declare avec [(section, {})] fait
echouer le chargement de la configuration de Spyder au demarrage, avec la boite "Une erreur s'est
produite lors du chargement des options de configuration de Spyder. Vous devez les reinitialiser" -
et le seul bouton propose efface TOUTE la configuration de l'utilisateur, disposition des panneaux
comprise (constate en direct le 20/07/2026 sur le greffon Pyxel). La section accueille aussi l'option
"<greffon>/enable" par laquelle Spyder desactive un greffon tiers depuis Preferences > Greffons.
"""

CONF_SECTION = "smartos_stop"

CONF_DEFAULTS = [(CONF_SECTION, {
    # Rendre la barre visible au TOUT PREMIER affichage (une nouvelle barre d'outils est
    # masquee par defaut par Spyder), puis respecter le choix de l'utilisateur. Cf. plugin.py :
    # la visibilite n'est forcee que tant que ce drapeau est False, et il passe a True juste apres.
    "_shown_once": False,
})]

# Regles de numerotation (identiques a celles des greffons livres avec Spyder) : changer la valeur
# par defaut d'une option => version MINEURE ; supprimer/renommer une option => version MAJEURE ;
# ajouter une option => rien a faire. Le numero ne revient JAMAIS en arriere (Spyder compare a la
# version stockee dans ~/.config/spyder-py3/plugins/<section>/spyder.ini et une version plus
# ancienne le fait echouer au chargement).
CONF_VERSION = "1.0.0"
