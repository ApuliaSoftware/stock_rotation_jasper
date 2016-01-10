# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Apulia Software S.r.l. (<info@apuliasoftware.it>)
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


from osv import fields, osv, orm
from tools.translate import _
import time


class temporary_product_rotation(orm.Model):
    # temporary table for data manipulation

    _name = 'temporary.product_rotation'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company'),
        'product_id': fields.many2one('product.product', 'Product'),
        #'date': fields.date('Date'),
        'month': fields.integer('Month'),
        'quantity': fields.float('Quantity'),
        'user_id': fields.many2one('res.users', 'User'),
    }

    def _clean_data(self, cr, uid, context):
        ids = self.search(cr, uid, [('user_id', '=', uid)])
        self.unlink(cr, uid, ids, context)
        return True

    def load_data(self, cr, uid, ids, parameters, context=None):
        self._clean_data(cr, uid, context)
        sale_obj = self.pool['sale.order']
        sale_line_obj = self.pool['sale.order.line']
        product_ids = []
        sale_ids = sale_obj.search(cr, uid, [
            ('date_order', '>=', parameters.year.date_start),
            ('date_order', '<=', parameters.year.date_stop),
        ])
        if parameters.product_ids:
            product_ids = [p.id for p in parameters.product_ids]
        if parameters.category_ids:
            product_ids = product_obj.search(
                cr, uid, ['|', ('categ_id', 'in', parameters.category_ids),
                          ('id', 'in', product_ids)])
        args = [('order_id', 'in', sale_ids),
                ('state', 'not in', ('draft', 'sent', 'cancel')),]
        if product_ids:
            args.append(('product_id', 'in', product_ids))
        sale_line_ids = sale_line_obj.search(cr, uid, args)
        sale_lines = sale_line_obj.browse(cr, uid, sale_line_ids)

        result = []
        for line in sale_lines:
            vals = {
                'company_id': line.order_id.company_id.id,
                'product_id': line.product_id.id,
                #'date': line.order_id.date_order,
                'month': line.order_id.date_order[5:][:2],
                'quantity': line.product_uom_qty,
                'user_id': uid,
            }
            result.append(self.create(cr, uid, vals, context))
        return result


class wizard_print_stockrotation(orm.TransientModel):

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(
            cr, uid, context=ctx)
        return period_ids

    _name = "wizard.print.stockrotation"

    _columns = {
        'category_ids': fields.many2many(
            'product.category',
            'product_category_rel', 'category_id', 'rotation_id',
            'Categories',
            help='Select categories you want retrieve products from'),
        'product_ids': fields.many2many(
            'product.product',
            'product_rel', 'product_id', 'rotation_id',
            'Products',
            help='Select products you want to print or none for all'),
        'year': fields.many2one(
                'account.fiscalyear', 'Fiscal Year', required=True),
        }

    _defaults = {
        #'start_date': fields.date.context_today,
        }

    def start_printing(self, cr, uid, ids, context={}):
        parameters = self.browse(cr, uid, ids, context)[0]
        data_ids = self.pool['temporary.product_rotation'].load_data(
            cr, uid, ids, parameters, context)
        if data_ids:
            data = {}
            data['ids'] = data_ids
            data['model'] = 'temporary.product_rotation'
            data['parameters'] = {
                'start_date': parameters.year.date_start,
                'end_date': parameters.year.date_stop,
            }
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'stock_rotation_jr',
                'datas': data,
            }
        else:
            raise osv.except_osv(_('Error !'), _('Nothing To Print'))
