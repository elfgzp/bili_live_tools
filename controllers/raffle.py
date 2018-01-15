# -*- coding: utf-8 -*-

import json

from odoo import http
from odoo.http import request


class RaffleJoin(http.Controller):
    @http.route('/raffle/join', type='http', auth='public', methods=['GET'], csrf=True)
    def get(self, account_id, room_id, raffle_extend_id):
        try:
            request.env['bili_live_tools.raffle'].join_raffle(account_id, room_id, raffle_extend_id)
        except:
            return json.dumps({'success': 0})
        else:
            return json.dumps({'success': 1})
