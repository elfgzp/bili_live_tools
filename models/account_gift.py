# -*- coding:utf-8 -*-

import time
import json
from math import ceil

from odoo import models, fields, api, exceptions

from ..utils import get_room_info


class AccountGift(models.Model):
    _name = 'bili_live_tools.account_gift'
    _description = u'账户礼物'
    _order = 'gift_id, expire_at, amount'

    bag_id = fields.Integer('包裹编号', index=True, required=True)
    account_id = fields.Many2one('bili_live_tools.account', string='账户', index=True, required=True)
    gift_id = fields.Many2one('bili_live_tools.gift', string='礼物', index=True, required=True)
    amount = fields.Integer('数量', track_visibility='onchange', index=True, required=True, default=0)
    expire_at = fields.Integer('过期时间', index=True)
    residue_time = fields.Char(' ', compute='_compute_residue_time')

    _sql_constraints = [(
        'bili_live_tools_account_gift_unique',
        'UNIQUE (account_id, bag_id, gift_id)',
        '账户礼物已存在!'
    )]

    @api.depends('expire_at')
    def _compute_residue_time(self):
        for each_record in self:
            residue_time = int(ceil((each_record.expire_at - time.time()) / 86400))
            if residue_time < 0:
                each_record.residue_time = '已过期'
            elif residue_time == 1:
                each_record.residue_time = '今天'
            else:
                each_record.residue_time = '%s天' % residue_time

    def record_account_gift(self, account_id, bag_id, gift_extend_id, gift_name, gift_type, amount, expire_at):
        gift = self.env['bili_live_tools.gift'].search([
            ('gift_extend_id', '=', gift_extend_id)
        ])
        if not gift:
            gift = self.env['bili_live_tools.gift'].create({
                'gift_extend_id': gift_extend_id,
                'name': gift_name,
                'type': gift_type
            })

        account_gift = self.search([
            ('bag_id', '=', bag_id),
            ('account_id', '=', account_id),
            ('gift_id', '=', gift.id)
        ])

        if not account_gift:
            self.create({
                'bag_id': bag_id,
                'account_id': account_id,
                'gift_id': gift.id,
                'amount': amount,
                'expire_at': expire_at
            })
        else:
            account_gift.write({
                'amount': amount,
                'expire_at': expire_at,
            })

    def send_all_account_gift(self, room_id, sub_account=True):
        account_gift = self.search([
            ('account_id.sub_account', '=', sub_account),
            ('amount', '>', 0),
            ('expire_at', '>=', int(time.time()))
        ])
        room_id = 264
        if account_gift:
            room_info = get_room_info(room_id=room_id)
            if room_info:
                room_id, room_uid = room_info['room_id'], room_info['uid']
                for each_gift in account_gift:
                    try:
                        result, msg = each_gift.send_gift(room_id, room_uid, self.amount)
                        if result:
                            each_gift.write({'amount': each_gift.amount - self.amount})
                        else:
                            raise exceptions.ValidationError(msg)
                    except Exception as e:
                        pass
                    else:
                        self.env.cr.commit()

    def send_gift(self, room_id, room_uid, amount):
        if self.account_id.status == 'logged':
            cookies_dict = self.account_id.cookies_dict()
            try:
                if cookies_dict:
                    payload = {
                        'uid': cookies_dict.get('DedeUserID', ''),
                        'gift_id': self.gift_id.gift_extend_id,
                        'ruid': room_uid,
                        'gift_num': amount,
                        'bag_id': self.bag_id,
                        'platform': 'pc',
                        'biz_code': 'live',
                        'biz_id': room_id,
                        'rnd': int(time.time()),
                        'storm_beat_id': 0,
                        'metadata': '',
                        'token': '',
                        'csrf_token': cookies_dict.get('bili_jct', '')
                    }
                    response = self.account_id.request(
                        url='http://api.live.bilibili.com/gift/v2/live/bag_send',
                        method='POST',
                        data=payload,
                    )
            except Exception as e:
                pass
            else:
                if response['code'] == 0 and response['msg'] == 'success':
                    return True, response['msg']
                else:
                    return False, response['msg']

    def send_selected_gift(self):
        context = self._context.copy()
        context['default_amount'] = self.amount
        context['active_ids'] = [self.id]
        return {
            'name': u'赠送礼物',
            'type': 'ir.actions.act_window',
            'res_model': 'bili_live_tools.send_gift_wizard',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('bili_live_tools.bili_live_tools_send_gift_wizard_view_form').id,
            'context': context,
            'target': 'new'
        }
