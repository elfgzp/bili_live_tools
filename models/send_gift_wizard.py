# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

from ..utils import get_room_info


class SendGiftWizard(models.TransientModel):
    _name = 'bili_live_tools.send_gift_wizard'
    _description = u'赠送礼物'

    room_id = fields.Integer('直播间号')
    amount = fields.Integer('数量')

    def apply(self):
        if self._context.get('clean_gift'):
            account_ids = self._context.get('active_ids')
            account = self.env['bili_live_tools.account'].browse(account_ids)
            account.clean_gift(self.room_id)
        else:
            room_info = get_room_info(room_id=self.room_id)
            if room_info:
                room_id, room_uid = room_info['room_id'], room_info['uid']
                account_gift = self.env['bili_live_tools.account_gift'].browse(self._context['active_ids'])
                for each_gift in account_gift:
                    result, msg = each_gift.send_gift(room_id, room_uid, self.amount)
                    if result:
                        each_gift.write({'amount': each_gift.amount - self.amount})
                    else:
                        raise exceptions.ValidationError(msg)
            else:
                raise exceptions.ValidationError('房间不存在!')
