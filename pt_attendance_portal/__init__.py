
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

# Import controllers and models for module initialization
from . import controllers
from . import models

def uninstall_hook(env):
    """Clean up geofence view references when module is uninstalled"""
    # Remove geofence_view from view_mode in ir_act_window records
    env.cr.execute("UPDATE ir_act_window "
               "SET view_mode=replace(view_mode, ',geofence_view', '')"
               "WHERE view_mode LIKE '%,geofence_view%';")
    env.cr.execute("UPDATE ir_act_window "
               "SET view_mode=replace(view_mode, 'geofence_view,', '')"
               "WHERE view_mode LIKE '%geofence_view,%';")
    # Delete any remaining geofence_view only records
    env.cr.execute("DELETE FROM ir_act_window "
               "WHERE view_mode = 'geofence_view';")

def pre_init_check(cr):
    """Verify Odoo version compatibility before module installation"""
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='18.0':
        raise UserError('Module support Odoo series 18.0 found {}.'.format(server_serie))
    return True