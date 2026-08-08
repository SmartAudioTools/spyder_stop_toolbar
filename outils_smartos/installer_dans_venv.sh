#!/bin/bash
# Installation de CE greffon dans le venv Spyder d'une machine SmartOS (mecanisme .pth
# "editable" : le greffon reste dans ce depot, seul un pointeur part dans site-packages).
# Sorti d'installation_SmartPythonEditor.sh le 08/08/2026 (demande utilisateur : les notes et
# verifications de chaque greffon vivent dans SON depot) - le script SmartOS n'est plus qu'un
# appel d'une ligne vers ce fichier. L'installation DISTRIBUEE (install.sh du fork
# SmartPythonEditor) n'utilise PAS ce script : elle passe par pip.
#
# Usage : installer_dans_venv.sh <python du venv Spyder> <sans_tests true|false> \
#                                <install_spyder_plugin.py> <spyder_config_set.py> <spyder.ini>
set -u
SPYDER_PYTHON="${1:?python du venv Spyder}"
SANS_TESTS="${2:-true}"
OUTIL_INSTALL="${3:?chemin de install_spyder_plugin.py}"
OUTIL_CONFIG="${4:?chemin de spyder_config_set.py}"
SPYDER_INI="${5:?chemin du spyder.ini}"
PLUGIN_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.." && pwd)"

PAQUET="spyder_stop_toolbar"; CLASSE="StopToolbar"; NOM_ATTENDU="smartos_stop"; BARRE="smartos_stop_toolbar"
if [ ! -f "$PLUGIN_DIR/pyproject.toml" ]; then
  echo "ERREUR : plugin introuvable dans $PLUGIN_DIR - abandon." >&2
  exit 1
fi

if [ ! -x "$SPYDER_PYTHON" ]; then
  echo "ERREUR : $SPYDER_PYTHON introuvable." >&2
  echo "         Installez d'abord Spyder (./installation_SmartPythonEditor.sh)." >&2
  exit 1
fi
echo "Environnement Spyder cible : $SPYDER_PYTHON"

# --- Verification de chargement ----------------------------------------------
if [ "$SANS_TESTS" = false ]; then
  echo
  echo "--- Import du greffon $PAQUET et construction de son icone ---"
  # QT_QPA_PLATFORM=offscreen : les icones qtawesome exigent un QApplication mais
  # pas d'affichage, pour rester utilisable depuis une console ou en SSH.
  QT_QPA_PLATFORM=offscreen PYTHONPATH="$PLUGIN_DIR" "$SPYDER_PYTHON" -c "
from qtpy.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])

from $PAQUET.spyder.plugin import $CLASSE
assert $CLASSE.NAME == '$NOM_ATTENDU'
assert not $CLASSE.get_icon().isNull()

# Les identifiants d'action des cibles d'arret sont ecrits en clair dans le greffon
# Stop (il ne veut dependre d'aucune d'elles) : on verifie qu'ils existent toujours
# cote Spyder, sinon le bouton cesserait silencieusement d'arreter ces cibles.
if '$PAQUET' == 'spyder_stop_toolbar':
    from spyder.plugins.debugger.widgets.main_widget import DebuggerWidgetActions
    from spyder.plugins.profiler.widgets.main_widget import ProfilerWidgetActions
    assert DebuggerWidgetActions.Stop == 'debug stop', DebuggerWidgetActions.Stop
    assert ProfilerWidgetActions.Stop == 'stop_action', ProfilerWidgetActions.Stop
print('OK  le greffon $PAQUET se charge et son icone se construit')
" || { echo "ERREUR : le greffon ne se charge pas - installation annulee." >&2; exit 1; }
fi

# --- Installation ------------------------------------------------------------
echo
# ⚠ PAS de "pip install" ici : le venv pyenv de Spyder est construit a partir d'un
# requirements fige qui NE CONTIENT PAS setuptools (cf. l'en-tete de
# install_spyder_plugin.py). install_spyder_plugin.py ecrit directement ce que
# produirait une installation "editable" : un .pth vers le dossier du depot + un
# .dist-info portant le point d'entree - exactement ce que lit
# spyder/app/find_plugins.py.
python3 "$OUTIL_INSTALL" \
    "$PLUGIN_DIR" "$SPYDER_PYTHON" || {
  echo "ERREUR : l'installation du plugin a echoue." >&2; exit 1; }

# --- Barre visible des le PREMIER demarrage ----------------------------------
# Spyder n'affiche au demarrage que les barres listees dans
# toolbar/last_visible_toolbars ; toute barre absente est masquee, case decochee.
# On AJOUTE a la liste ("+=") plutot que de la reecrire : les barres que
# l'utilisateur a activees par ailleurs doivent rester. Le greffon a par ailleurs
# son propre filet (drapeau _shown_once, cf. plugin.py) pour une configuration
# deja deployee.
python3 "$OUTIL_CONFIG" \
    "$SPYDER_INI" \
    "toolbar/last_visible_toolbars+=$BARRE"

echo
echo "Greffon '$PAQUET' installe. Dans Spyder : menu Affichage > Barres d'outils."
