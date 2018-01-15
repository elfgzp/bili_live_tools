# -*- coding: utf-8 -*-

import json

from odoo import http
from odoo.http import request


class AccountAmount(http.Controller):
    @http.route('/account/amount', type='http', auth='public', methods=['GET'], csrf=True)
    def get(self):
        try:
            amount = request.env['bili_live_tools.account'].search_count([('status', '=', 'logged')])
        except Exception as e:
            return json.dumps({'success': 0, 'data': e})
        else:
            return json.dumps({'success': 1, 'data': amount})


class AccountCookies(http.Controller):
    @http.route('/account/cookies', type='http', auth='public', methods=['GET'], csrf=True)
    def get(self, offset=0, limit=100):
        try:
            account_ids = request.env['bili_live_tools.account'].search([
                ('status', '=', 'logged')
            ], offset=int(offset), limit=int(limit))
        except Exception as e:
            return json.dumps({'success': 0, 'data': e})
        else:
            return json.dumps({
                'success': 1,
                'data': [{
                    'id': a.id,
                    'name': a.name,
                    'cookies': a.cookies
                } for a in account_ids]
            })
