#!/usr/bin/env python
#-*- coding: utf-8 -*-

# To use exit...
import sys
import locale
import gettext

class Locale:
    def __init__(self, logs, config):
        self.logs = logs
        paramloc = False
        toloadloc = False
        self.localefallback = 'en_GB.UTF-8'
        localias = {}
        localias['fr_FR'] = ['fr_FR', 'fr_BE', 'fr_CA', 'fr_CH', 'fr_LU', 'fr_MC']
        localias['en_GB'] = ['en_GB', 'en_029', 'en_AU', 'en_BZ', 'en_CA', 'en_GB', 'en_IE', \
                'en_IN', 'en_JM', 'en_MY', 'en_NZ', 'en_PH', 'en_SG', 'en_TT', 'en_US', \
                'en_ZA', 'en_ZW']
        localias['es_ES'] = ['es_ES', 'es_AR', 'es_BO', 'es_CL', 'es_CO', 'es_CR', 'es_DO', \
                'es_EC', 'es_GT', 'es_HN', 'es_MX', 'es_NI', 'es_PA', 'es_PE', 'es_PR', 'es_PY', \
                'es_SV', 'es_US', 'es_UY', 'es_VE']
        localias['de_DE'] = ['de_DE', 'de_CH']
        localias['it_IT'] = ['it_IT', 'it_CH']
        localias['nl_NL'] = ['nl_NL', 'nl_BE']

        if config.get_value('SectionGlobals', 'locale'):
            paramloc = config.get_value('SectionGlobals', 'locale')
            self.logs.debug(f"You requested to load following locale {paramloc}")
        else:
            paramloc = locale.getdefaultlocale() # get current user locale
            paramloc = paramloc[0]#Get only first part (remove char encoding)
            self.logs.debug("Your detected locale name is \"{paramloc}\".")

        for alloc, alias in localias.items(): #Search which main locale it belongs
            if paramloc and paramloc in alias: # And load it
                toloadloc = f"{alloc}.UTF-8"
                self.logs.debug(f"Your locale is mapped on locale : \"{toloadloc}\".")
        # If at this stage toloadloc is not defined, use fallback (english)
        if not toloadloc:
            toloadloc = self.localefallback
            self.logs.warning(
                    f"Unable to map your locale. Using fallback locale : \"{toloadloc}\".")
        kwargs = {}
        if sys.version_info[0] < 3:
            # In Python 2, ensure that the _() that gets installed into built-ins
            # always returns unicodes.  This matches the default behavior under
            # Python 3, although that keyword argument is not present in the
            # Python 3 API.
            kwargs['unicode'] = True
        self.translator = gettext.translation('pydarts', 'locales', [toloadloc])
        self.translator.install( **kwargs)
        self.lang = toloadloc[0:2:1]

    #
    # Return requested string
    #
    def translate(self, string, game=None):
        if _(string) != string:
            return _(string)
        elif game is not None and _(string.replace(f'{game}', 'AllGame')) != string.replace(f'{game}', 'AllGame'):
            return _(string.replace(f'{game}', 'AllGame'))
        return string
