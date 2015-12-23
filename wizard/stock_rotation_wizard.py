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

    _name = 'temporary.product_rotation'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company'),
        'product_id': fields.char('Number', size=64),
        'date': fields.date('Date'),
        'invoice_number': fields.char('Invoice Number', size=64),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID'),
        'invoice_date': fields.date('Invoice Date'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'invoice_type': fields.char('Invoice Type', size=64),
        'invoice_total': fields.float('Invoice Total'),
        'tax_id': fields.many2one('account.tax', 'Tax ID'),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Account'),
        'amount_untaxed': fields.float('Amount Untaxed'),
        'amount_tax': fields.float('Amount Tax'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'period_id': fields.many2one('account.period', 'Period'),
        }

    def _pulisci(self, cr, uid, context):
        ids = self.search(cr, uid, [])
        self.unlink(cr, uid, ids, context)
        return True

    def load_data(self, cr, uid, ids, paramters, context=None):
        self._pulisci(cr, uid, context)
        #~ move_obj = self.pool.get('account.move')
        invoice_obj = self.pool.get('account.invoice')
        #~ move_ids = move_obj.search(cr, uid, [
            #~ ('journal_id', 'in', [j.id for j in paramters.journal_ids]),
            #~ ('period_id', 'in', [p.id for p in paramters.period_ids]),
            #~ ('state', '=', 'posted'),
            #~ ], order='date')
        invoice_ids = invoice_obj.search(cr, uid, [
            ('journal_id', 'in', [j.id for j in paramters.journal_ids]),
            ('period_id', 'in', [p.id for p in paramters.period_ids]),
            ('state', 'not in', ('posted', 'draft',
                                 'cancel', 'proforma', 'proforma2')),
            ], order='registration_date')
        if not invoice_ids:
            #~ TODO
            return False
        line_ids = []
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
            tax_sign = 1
            if invoice.state in ('proforma', 'proforma2'):
                continue
            invoice_number = invoice.number
            if invoice.type in ('in_invoice', 'out_refund'):
                tax_sign = -1
                invoice_number = invoice.supplier_invoice_number
            for tax_line in invoice.tax_line:
                vals = {
                    'company_id': invoice.company_id.id,
                    'name': invoice.move_id.name,
                    'date': invoice.registration_date,
                    'invoice_number': invoice_number,
                    'invoice_id': invoice.id,
                    'invoice_date': invoice.date_invoice,
                    'partner_id': invoice.partner_id.id,
                    'invoice_type': invoice.type,
                    'invoice_total': invoice.amount_total,
                    #~ 'tax_id': move.account_tax_id.id,
                    'tax_code_id': tax_line.tax_code_id.id,
                    'amount_untaxed': tax_line.base * tax_sign,
                    'amount_tax': tax_line.amount * tax_sign,
                    'journal_id': invoice.journal_id.id,
                    'period_id': invoice.period_id.id,
                    }
                line_ids.append(self.create(cr, uid, vals, context))
        ok = self.pool.get('temporary.stockrotation.total').load_data(
            cr, uid, line_ids, context)
        if not ok:
            raise osv.except_osv(_('Error!'), _('Failed to load data'))
        return True


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
            'Journals',
            help='Select products you want to print or none for all'),
        'start_date': fields.datetime('Start date', required=True),
        'end_date': fields.datetime('End date', required=True),
        }

    _defaults = {
        'start_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def start_printing(self, cr, uid, ids, context={}):
        parameters = self.browse(cr, uid, ids, context)[0]
        ok = self.pool.get('temporary.product_rotation').load_data(
            cr, uid, ids, parameters, context)
        if ok:
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['form'] = {}
            data['form'][
                'parameters'] = {'last_page': parameters.fiscal_page_base,
                                 'last_year': parameters.fiscal_year_page,
                                 }
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'stock_rotation_jr',
                    'datas': data,
                    }
        else:
            raise osv.except_osv(_('Error !'), _('Nothing To Print'))
        return {'type': 'ir.actions.act_window_close'}
