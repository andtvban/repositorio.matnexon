################################################################################
#      Copyright (C) 2019 drinfernoo                                           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################

import xbmc
import xbmcgui

import os
import re

from resources.libs.common.config import CONFIG


def wizard_update():
    from resources.libs import check
    from resources.libs.common import logging
    from resources.libs.common import tools
    from resources.libs.gui import window

    dialog = xbmcgui.Dialog()
    progress_dialog = xbmcgui.DialogProgress()

    response = tools.open_url(CONFIG.BUILDFILE, check=True)

    if response:
        try:
            wid, ver, zip = check.check_wizard('all')
        except:
            return
        if ver > CONFIG.ADDON_VERSION:
            yes = dialog.yesno(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]Hay una nueva versión del {1}!'.format(CONFIG.COLOR2, CONFIG.ADDONTITLE)
                                   +'\n'+'¿Quieres descargar [COLOR {0}]v{1}[/COLOR]?[/COLOR]'.format(CONFIG.COLOR1, ver),
                                   nolabel='[B][COLOR red]Recuérdame Más Tarde[/COLOR][/B]',
                                   yeslabel="[B][COLOR springgreen]Actualizar Wizard[/COLOR][/B]")
            if yes:
                from resources.libs import db
                from resources.libs.common import tools

                logging.log("[Wizard de Actualización Automática] Instalación Wizard v{0}".format(ver))
                progress_dialog.create(CONFIG.ADDONTITLE, '[COLOR {0}]Descargando Actualización...'.format(CONFIG.COLOR2)
                                        +'\n'+''
                                        +'\n'+'Espere por favor[/COLOR]')
                lib = os.path.join(CONFIG.PACKAGES, '{0}-{1}.zip'.format(CONFIG.ADDON_ID, ver))
                try:
                    os.remove(lib)
                except:
                    pass
                from resources.libs.downloader import Downloader
                from resources.libs import extract
                Downloader().download(zip, lib)
                xbmc.sleep(2000)
                progress_dialog.update(0, '\n'+"Instalación {0} actualizar".format(CONFIG.ADDONTITLE))
                percent, errors, error = extract.all(lib, CONFIG.ADDONS, True)
                progress_dialog.close()
                xbmc.sleep(1000)
                db.force_check_updates(auto=True, over=True)
                xbmc.sleep(1000)
                logging.log_notify(CONFIG.ADDONTITLE,
                                   '[COLOR {0}]Add-on actualizado[/COLOR]'.format(CONFIG.COLOR2))
                logging.log("[Wizard de Actualización Automática] Wizard actualizado a v{0}".format(ver))
                tools.remove_file(os.path.join(CONFIG.ADDON_DATA, 'settings.xml'))
                window.show_save_data_settings()
            else:
                logging.log("[Wizard de Actualización Automática] Instalar Nuevo Wizard Ignorado: {0}".format(ver))
        else:
            logging.log("[Wizard de Actualización Automática] Sin Nueva Versión v{0}".format(ver))
    else:
        logging.log("[Wizard de Actualización Automática] La URL del archivo del Wizard no es válida: {0}".format(CONFIG.BUILDFILE))


def addon_updates(do=None):
    setting = '"general.addonupdates"'
    if do == 'set':
        query = '{{"jsonrpc":"2.0", "method":"Settings.GetSettingValue","params":{{"setting":{0}}}, "id":1}}'.format(setting)
        response = xbmc.executeJSONRPC(query)
        match = re.compile('{"value":(.+?)}').findall(response)
        if len(match) > 0:
            default = match[0]
        else:
            default = 0
        CONFIG.set_setting('default.addonupdate', str(default))
        query = '{{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{{"setting":{0},"value":{1}}}, "id":1}}'.format(setting, '2')
        response = xbmc.executeJSONRPC(query)
    elif do == 'reset':
        try:
            value = int(float(CONFIG.get_setting('default.addonupdate')))
        except:
            value = 0
        if value not in [0, 1, 2]:
            value = 0
        query = '{{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{{"setting":{0},"value":{1}}}, "id":1}}'.format(setting, value)
        response = xbmc.executeJSONRPC(query)
        
        
def toggle_addon_updates():
    from resources.libs.common import logging
    
    setting = '"general.addonupdates"'
    selected = 0
    options = ['Instalar actualizaciones automáticamente', 'Notificar, pero no instalar actualizaciones', 'Nunca comprobar si hay actualizaciones']
    set_query = '{{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{{"setting":"general.addonupdates","value":{0}}}, "id":1}}'
    
    dialog = xbmcgui.Dialog()
    
    selected = dialog.select(CONFIG.ADDONTITLE, options)
            
    logging.log_notify(CONFIG.ADDONTITLE, 'Las actualizaciones cambiaron a "{0}"'.format(options[selected]))
    xbmc.executeJSONRPC(set_query.format(selected))
