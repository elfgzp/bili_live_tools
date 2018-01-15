# -*- coding: utf-8 -*-

from odoo import models, fields, api
from ..utils import RAFFLE_NOTICE_URL


class Raffle(models.Model):
    _name = 'bili_live_tools.raffle'
    _description = u'抽奖'
    _order = 'raffle_time desc'

    account_id = fields.Many2one('bili_live_tools.account', string='账户', index=True, required=True)
    room_id = fields.Integer()
    raffle_extend_id = fields.Integer()
    gift_id = fields.Many2one('bili_live_tools.gift', string='礼物', index=True)
    amount = fields.Integer('数量', track_visibility='onchange', index=True, default=0)
    gift_from = fields.Char()
    raffle_time = fields.Datetime('抽奖时间')
    get_raffle_time = fields.Datetime('获奖时间')
    checked = fields.Boolean('已开奖', index=True, default=False)

    @api.model
    def join_raffle(self, account_id, room_id, raffle_extend_id):
        try:
            self.create({
                'account_id': account_id,
                'room_id': room_id,
                'raffle_extend_id': raffle_extend_id,
                'raffle_time': fields.Datetime.now(),
            })
        except Exception as e:
            pass
        else:
            self.env.cr.commit()

    def check_all_raffle(self):
        raffle = self.search([('checked', '=', False)])
        if raffle:
            raffle.check_raffle()

    @api.multi
    def check_raffle(self):
        for each_record in self:
            params = {
                'roomid': each_record.room_id,
                'raffleId': each_record.raffle_extend_id
            }
            r = each_record.account_id.request(RAFFLE_NOTICE_URL, 'GET', params=params)
            if r and r['data']:
                if r['data']['gift_id'] > 0:
                    each_record.get_raffle(
                        gift_extend_id=r['data']['gift_id'],
                        gift_name=r['data']['gift_name'],
                        gift_type=r['data']['gift_type'],
                        amount=r['data']['gift_num'],
                        gift_from=r['data']['gift_from']
                    )
                elif r['data']['gift_id'] == -1:
                    each_record.write({'checked': True})

    def get_raffle(self, gift_extend_id, gift_name, gift_type, amount, gift_from):
        gift = self.env['bili_live_tools.gift'].search([
            ('gift_extend_id', '=', gift_extend_id)
        ])
        try:
            if not gift:
                gift = self.env['bili_live_tools.gift'].create({
                    'gift_extend_id': gift_extend_id,
                    'name': gift_name,
                    'type': gift_type
                })

            self.write({
                'gift_id': gift.id,
                'amount': amount,
                'gift_from': gift_from,
                'get_raffle_time': fields.Datetime.now(),
                'checked': True
            })
        except Exception as e:
            pass
        else:
            self.env.cr.commit()
