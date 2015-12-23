# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015s Apulia Software S.r.l. (<info@apuliasoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Stock products rotation with Jasper Reports",
    'version': '0.1',
    'category': 'stock',
    'description': """Prints products rotation in stock with Jasper Reports""",
    'author': 'Apulia Software S.r.l.',
    'website': 'www.apuliasoftware.it',
    'license': 'AGPL-3',
    "depends": ['jasper_reports',
                'stock'
                ],
    "init_xml": ['wizard/stock_rotation_view.xml',
                 'report.xml',
                 'security/ir.model.access.csv',
                 ],
    "update_xml": [],
    "demo_xml": [],
    "active": False,
    "installable": True
}
