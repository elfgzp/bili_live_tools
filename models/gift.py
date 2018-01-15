# -*- coding:utf-8 -*-

from odoo import models, fields


class Gift(models.Model):
    _name = 'bili_live_tools.gift'
    _description = u'礼物'

    gift_extend_id = fields.Integer('礼物编号', index=True, required=True)
    name = fields.Char('礼物', index=True, required=True)
    type = fields.Integer()

    _sql_constraints = [(
        'bili_live_tools_gift_extend_id_unique',
        'UNIQUE (gift_extend_id)',
        '礼物编号已存在!'
    )]
