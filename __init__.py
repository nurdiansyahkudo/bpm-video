#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from . import controllers
from . import models
from . import wizard

def pre_init_check(cr):
    from odoo.release import series
    from odoo.exceptions import ValidationError

    if not(series > '16.0' and series <= '17.0'):
        raise ValidationError('Module support Odoo series 17.0 found {}.'.format(series))
