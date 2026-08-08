# -*- coding: utf-8 -*-
"""Greffon "Barre Stop" : UN bouton (carre rouge fuchsia) qui arrete TOUT ce qui peut tourner -
execution normale, debogage, profilage (cProfile), VizTracer, Python Tutor, analyse de code.
Spyder eparpille ces arrets : un bouton dans la barre du debogueur, un autre dans le panneau
Profileur, un troisieme dans le coin de la Console IPython, rien du tout pour l'analyse de code.
Il fallait savoir QUI tourne pour savoir OU cliquer.

Contexte : item 3 de CachyOS/Documentation/TODO - Spyder - cosmetique.txt, demande de
l'utilisateur du 26/07/2026. Issu de la SCISSION du greffon "Commandes SmartOS" (08/08/2026,
demande de l'utilisateur) : la barre Stop d'un cote (ici), le Docteur et le report des remarques
pylint dans la marge de l'autre (spyder_code_analysis) - deux fonctions independantes, activables
separement depuis Preferences > Greffons.

POURQUOI UN GREFFON EXTERNE ET NON UN PATCH
    C'est un AJOUT (une barre, un bouton), pas la modification d'un comportement existant :
    un greffon survit aux montees de version de Spyder, un patch sur site-packages non (regle du
    depot). Aucun code de Spyder n'est touche : on ne fait que declencher des actions et des
    methodes publiques deja la.

POURQUOI self.get_main().get_plugin(...) ET NON self.get_plugin(...)
    SpyderPluginV2.get_plugin() EXIGE que le nom figure dans REQUIRES ou OPTIONAL, et leve sinon -
    y compris pour un greffon absent. Or les cibles du bouton Stop sont toutes facultatives :
    chacune peut etre desactivee depuis Preferences > Greffons (Debogueur, Profileur, Analyse de
    code) ou simplement pas installee (Python Tutor, VizTracer). Les declarer en OPTIONAL ferait
    dependre notre graphe de dependances de greffons tiers. MainWindow.get_plugin(nom,
    error=False), lui, ne verifie aucune declaration et rend None si absent - c'est ce que fait
    deja le patch du menu burger (patch_spyder_burger_menu.py). Les cibles sont donc resolues AU
    CLIC, pas au demarrage : un greffon active entre-temps est pris en compte sans redemarrer.

POURQUOI LE BOUTON STOP RESTE TOUJOURS ACTIF
    Savoir s'il y a quelque chose a arreter demanderait d'interroger six greffons en permanence
    (aucun n'emet de signal commun "je tourne"), donc un minuteur perpetuel - pour un bouton dont
    l'appui a vide ne fait RIEN : chaque cible est testee avant d'etre touchee (action
    desactivee, processus non demarre, noyau au repos). Un stop toujours cliquable est aussi le
    comportement de la plupart des environnements de developpement.

TIMING
    La barre est creee dans on_plugin_available(Toolbar), donc AVANT que le plugin Toolbar ne
    construise le menu "Barres d'outils" (il le fait dans SON on_mainwindow_visible, en
    parcourant self._ADDED_TOOLBARS) : elle apparait ainsi dans Affichage > Barres d'outils et sa
    visibilite est memorisee comme celle des autres barres (last_visible_toolbars).
"""
import logging

import qtawesome as qta

from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.plugin_registration.decorators import (
    on_plugin_available, on_plugin_teardown)

from spyder_stop_toolbar.spyder.config import (
    CONF_DEFAULTS, CONF_SECTION, CONF_VERSION)
from spyder_stop_toolbar.spyder.translations import _

# ⚠ logger.debug() et RIEN d'autre : la console interne de Spyder traite toute ligne ecrite sur
# stderr comme une erreur et ouvre une fenetre "problème interne". logger.warning() et au-dessus y
# retombent faute de gestionnaire (regle du depot).
logger = logging.getLogger(__name__)

# Rouge fuchsia demande par l'utilisateur : franchement rouge, mais tire vers le magenta pour ne se
# confondre avec aucune autre icone de l'interface (le rouge d'erreur de Spyder, les points
# d'arret). Lisible sur les deux themes.
STOP_COLOR = "#FF0066"

# Reduction du carre pour qu'il fasse LA HAUTEUR DU CONTENU de l'icone de lancement du debogage
# (demande de l'utilisateur, chapitre "icones" du TODO cosmetique). Le carre plein de mdi occupe
# 66 % de la hauteur de son cadre, la fleche de debogage 58,6 % : cote a cote, le stop paraissait
# plus gros que tous ses voisins.
# ⚠ CETTE VALEUR EST MESUREE, PAS CHOISIE : hauteur d'ENCRE (boite englobante des pixels non
# transparents) des deux icones rendues a 256 px - 169 px pour le carre, 150 px pour le debogage,
# soit 150/169 = 0,888. Verifie ensuite en rendant le carre a ce facteur : 151 px, l'ecart d'un
# pixel sur 256 etant tres inferieur au pixel a la taille reelle du bouton. Re-mesurer si Spyder
# change son icone de debogage - le facteur depend d'ELLE, pas d'un gout.
STOP_SCALE = 0.888


class StopToolbar(SpyderPluginV2):
    """Barre d'outils "Stop" : un bouton qui arrete tout ce qui tourne."""

    NAME = "smartos_stop"  # doit etre identique au nom du point d'entree (pyproject.toml)
    REQUIRES = [Plugins.Toolbar]
    CONF_SECTION = CONF_SECTION
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION

    # Inchange depuis le greffon d'origine (scission du 08/08/2026) : cet identifiant figure dans
    # last_visible_toolbars des configurations existantes et dans l'ordre des barres impose par
    # patch_spyder_toolbar_order.py - le changer les casserait tous les deux.
    STOP_TOOLBAR_ID = "smartos_stop_toolbar"
    STOP_ACTION_ID = "smartos_stop_everything"

    # ---- SpyderPluginV2 API
    @staticmethod
    def get_name():
        return _("Barre Stop")

    @staticmethod
    def get_description():
        return _("Barre \"Stop\" : un bouton qui arrete execution, debogage, profilage, "
                 "VizTracer, Python Tutor et analyse de code.")

    @classmethod
    def get_icon(cls):
        return qta.icon("mdi.square", color=STOP_COLOR, scale_factor=STOP_SCALE)

    def on_initialize(self):
        self._toolbar = None
        self._stop_action = self.create_action(
            self.STOP_ACTION_ID,
            text=_("Tout arreter"),
            icon=qta.icon("mdi.square", color=STOP_COLOR, scale_factor=STOP_SCALE),
            tip=_("Arreter l'execution, le debogage, le profilage, VizTracer, Python Tutor et "
                  "l'analyse de code."),
            triggered=self.stop_everything,
        )

    @on_plugin_available(plugin=Plugins.Toolbar)
    def _on_toolbar_available(self):
        toolbar = self.get_plugin(Plugins.Toolbar)
        self._toolbar = toolbar.create_application_toolbar(self.STOP_TOOLBAR_ID, _("Stop"))
        toolbar.add_item_to_application_toolbar(
            self._stop_action, toolbar_id=self.STOP_TOOLBAR_ID)

    @on_plugin_teardown(plugin=Plugins.Toolbar)
    def _on_toolbar_teardown(self):
        toolbar = self.get_plugin(Plugins.Toolbar)
        toolbar.remove_item_from_application_toolbar(
            self.STOP_ACTION_ID, toolbar_id=self.STOP_TOOLBAR_ID)
        toolbar.remove_application_toolbar(self.STOP_TOOLBAR_ID)
        self._toolbar = None

    def on_mainwindow_visible(self):
        # Rendre la barre visible au TOUT PREMIER affichage : une barre d'outils nouvellement
        # creee est masquee par defaut (load_last_visible_toolbars la met a setVisible(False)) et
        # l'utilisateur aurait du aller la cocher. On force la visibilite UNE seule fois (drapeau
        # de configuration), via singleShot(0) pour passer APRES le load_last_visible_toolbars
        # synchrone du plugin Toolbar. Ensuite on respecte son choix : la visibilite suit
        # last_visible_toolbars comme pour les autres barres. Meme mecanique que
        # spyder_interpreter_toolbar.
        if self.get_conf("_shown_once", default=False) or self._toolbar is None:
            return
        from qtpy.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._toolbar.setVisible(True))
        self.set_conf("_shown_once", True)

    # ---- Barre "Stop"
    def stop_everything(self):
        """Arreter tout ce qui tourne, chaque cible etant testee avant d'etre touchee.

        Chaque arret est isole dans son propre try : une cible en erreur (greffon a moitie charge,
        API changee par une montee de version) ne doit pas empecher les autres de s'arreter.
        L'ORDRE compte pour les deux premieres : une session de debogage vit DANS le noyau
        IPython, on la termine proprement avant d'envisager d'interrompre le noyau.
        """
        for description, arret in (
            ("debogage", self._stop_debugging),
            ("profilage", self._stop_profiler),
            ("VizTracer", self._stop_viztracer),
            ("Python Tutor", self._stop_python_tutor),
            ("analyse de code", self._stop_code_analysis),
            ("execution", self._interrupt_kernel),
        ):
            try:
                arret()
            except Exception:
                logger.debug("Tout arreter : echec de l'arret du %s.", description, exc_info=True)

    @staticmethod
    def _trigger_if_active(widget, action_id):
        """Declencher une action de panneau si elle est reellement disponible.

        On s'appuie sur l'etat que le greffon proprietaire entretient lui-meme (son
        update_actions active/desactive son bouton d'arret selon qu'il tourne ou non) plutot que
        de redecouvrir de l'exterieur s'il y a quelque chose a arreter : c'est sa logique, elle
        reste juste apres une montee de version.
        """
        action = widget.get_action(action_id)
        if action.isEnabled() and action.isVisible():
            action.trigger()

    def _stop_debugging(self):
        debugger = self.get_main().get_plugin(Plugins.Debugger, error=False)
        if debugger is not None:
            # "debug stop" = DebuggerWidgetActions.Stop, active seulement pendant une session.
            self._trigger_if_active(debugger.get_widget(), "debug stop")

    def _stop_profiler(self):
        profiler = self.get_main().get_plugin(Plugins.Profiler, error=False)
        if profiler is not None:
            # "stop_action" = ProfilerWidgetActions.Stop, active seulement pendant un profilage.
            self._trigger_if_active(profiler.get_widget(), "stop_action")

    def _stop_viztracer(self):
        # Greffon de la pile SmartPythonEditor (depot spyder_viztracer) : il expose
        # stop_profiling(), qui tue le processus de tracage et le serveur de timeline.
        viztracer = self.get_main().get_plugin("viztracer_profiler", error=False)
        if viztracer is not None:
            viztracer.get_widget().stop_profiling()

    def _stop_python_tutor(self):
        # Greffon de la pile SmartPythonEditor (depot spyder_python_tutor) :
        # "python_tutor_stop" = PythonTutorActions.Stop, deployee seulement pendant une session.
        tutor = self.get_main().get_plugin("python_tutor", error=False)
        if tutor is not None:
            self._trigger_if_active(tutor.get_widget(), "python_tutor_stop")

    def _stop_code_analysis(self):
        pylint = self.get_main().get_plugin(Plugins.Pylint, error=False)
        if pylint is not None:
            # Sans effet si aucune analyse ne tourne (PylintWidget._kill_process n'est appele que
            # si _is_running()).
            pylint.stop_code_analysis()

    def _interrupt_kernel(self):
        """Interrompre le noyau de la console courante, mais SEULEMENT s'il execute.

        Sans ce test, un clic a vide enverrait un SIGINT a un noyau au repos (une
        KeyboardInterrupt dans la console pour rien) et ferait remonter la Console IPython au
        premier plan - interrupt_kernel() emet sig_switch_to_plugin_requested.
        """
        ipyconsole = self.get_main().get_plugin(Plugins.IPythonConsole, error=False)
        if ipyconsole is None:
            return
        widget = ipyconsole.get_widget()
        client = widget.get_current_client()
        if client is not None and client.is_client_executing():
            widget.interrupt_kernel()
