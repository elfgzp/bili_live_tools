# -*- coding: utf-8 -*-

import logging
import datetime
import requests
import time
from PIL import Image
import StringIO
import gevent
import gevent.pool
from odoo import models, fields, api, exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from .. import ocr
from ..utils import get_proxy, get_room_info, QUERY_FREE_SILVER, CAPTCHA_URL, \
    GET_FREE_SILVER, TV_URL, QUERY_RAFFLE_URL, \
    RAFFLE_URL

_logger = logging.getLogger(__name__)


class Account(models.Model):
    _name = 'bili_live_tools.account'
    _description = u'账号'
    _rec_name = 'login'
    _order = 'sub_account, status'

    name = fields.Char('名称')
    uid = fields.Integer('uid')
    login = fields.Char('账号', index=True, required=True)
    password = fields.Char('密码')
    cookies = fields.Char('Cookies')
    sub_account = fields.Boolean('是否是小号', index=True)
    status = fields.Selection(
        [
            ('logged', '已登录'),
            ('logout', '未登录'),
            ('logging', '正在登录'),
            ('failed', '登录失败')

        ]
        , string='状态', index=True, default='logout', track_visibility='onchange', required=True
    )
    last_update_time = fields.Integer('最后一次刷新时间', index=True, default=0)

    account_gift_ids = fields.One2many('bili_live_tools.account_gift', 'account_id', string='礼物',
                                       domain=[('amount', '>', 0), ('expire_at', '>=', int(time.time()))])
    account_gift_total = fields.Integer('礼物总数', compute='_compute_account_gift_total')
    gold_seed = fields.Integer('金瓜子', index=True, default=0)
    silver_seed = fields.Integer('银瓜子', index=True, default=0)

    phone_verification = fields.Boolean('是否绑定手机', index=True, default=True)
    free_sliver = fields.Boolean('宝箱瓜子是否领完', index=True, default=True)
    next_free_sliver_time = fields.Integer('下一次领取宝箱时间', index=True, default=0)

    _sql_constraints = [(
        'bili_live_tools_account_login_unique',
        'UNIQUE (login)',
        '账号已存在!'
    )]

    @api.multi
    def write(self, vals):
        cookies = vals.get('cookies')
        result = super(Account, self).write(vals)
        if cookies:
            self.login_cron()
        return result

    @api.model
    def create(self, vals):
        cookies = vals.get('cookies')
        record = super(Account, self).create(vals)
        if cookies:
            record.login_cron()
        return record

    @api.depends('account_gift_ids')
    def _compute_account_gift_total(self):
        for each_record in self:
            each_record.account_gift_total = sum(each_record.account_gift_ids.mapped(lambda r: r.amount))

    def request(self, url, method, params=None, data=None, headers=None, proxy_times=10):
        headers = headers if headers else {}
        headers.update({'Cookie': self.cookies})
        kwargs = dict(url=url, method=method, params=params, data=data, headers=headers, timeout=5)
        proxy = get_proxy()
        try_times = 0
        try:
            while proxy and proxy_times > try_times:
                proxy_times += 1
                kwargs['proxies'] = {'http': 'http://%s' % proxy, 'https': 'https://%s' % proxy}
                try:
                    response = requests.request(**kwargs)
                except:
                    proxy = get_proxy()
                else:
                    if response.status_code != 200:
                        proxy = get_proxy()
                    else:
                        break
            else:
                kwargs['proxies'] = None
                response = requests.request(**kwargs)
        except Exception as e:
            _logger.exception(e)
            return {}
        else:
            _logger.info(response.json())
            return response.json() if response.status_code == 200 else {'code': -1, 'msg': '', 'data': []}

    def cookies_dict(self):
        cookies_dict = {}
        try:
            cookies_dict = dict([key_val.split('=') for key_val in self.cookies.split('; ')])
        except:
            pass
        return cookies_dict

    @api.multi
    def login_cron(self):
        for each_record in self:
            self.env['ir.cron'].sudo().create({
                'name': '登录账户: %s' % each_record.login,
                'user_id': self.env.uid,
                'model': self._name,
                'function': '_update_status',
                'active': True,
                'priority': 0,
                'numbercall': 1,
                'nextcall': (datetime.datetime.utcnow() + datetime.timedelta(seconds=3)).strftime(DATETIME_FORMAT),
                'interval_type': 'minutes',
                'args': repr([each_record.id, ])
            })
        self.write({'status': 'logging'})

    def update_all_account_status(self):
        all_account = self.search([
            ('status', '=', 'logged'),
            ('last_update_time', '<=', int(time.time()) - 3600),

        ], limit=100)
        if all_account:
            all_account.update_status()

    @api.multi
    def update_status(self):
        for each_record in self:
            if each_record.cookies:
                each_record._update_status(each_record.id)
        self.write({'last_update_time': int(time.time())})

    def _update_status(self, account_id):
        account = self.browse(account_id)
        response = account.request(
            url='http://api.live.bilibili.com/User/getUserInfo',
            method='GET',

        )
        code = response['code']

        try:
            if code == 'REPONSE_OK':
                data = response['data']
                account.write({
                    'name': data['uname'],
                    'status': 'logged',
                    'gold_seed': data['gold'],
                    'silver_seed': data['silver']
                })
                account.update_gift()
            else:
                account.write({'status': 'failed'})
        except Exception as e:
            pass
        else:
            self.env.cr.commit()

    def update_gift(self):
        response = self.request(
            url='http://api.live.bilibili.com/gift/v2/gift/bag_list',
            method='GET',

        )
        code = response['code']
        if code == 0:
            data = response['data']
            gift_list = data.get('list', [])
            self.account_gift_ids.write({'amount': 0})
            for gift in gift_list:
                self.env['bili_live_tools.account_gift'].record_account_gift(
                    account_id=self.id,
                    bag_id=gift['bag_id'],
                    gift_extend_id=gift['gift_id'],
                    gift_name=gift['gift_name'],
                    gift_type=gift['gift_type'],
                    expire_at=gift['expire_at'],
                    amount=gift['gift_num']
                )

    def reset_all_free_silver(self):
        all_account = self.search([])
        if all_account:
            all_account.write({'free_sliver': True})

    def check_all_free_silver(self):
        all_account = self.search([
            ('status', '=', 'logged'),
            ('phone_verification', '=', True),
            ('free_sliver', '=', True),
            ('next_free_sliver_time', '<=', int(time.time())),
        ], limit=100)
        for each_account in all_account:
            try:
                each_account.query_free_silver()
            except Exception as e:
                pass

    def query_free_silver(self):
        r = self.request(QUERY_FREE_SILVER, 'GET')
        # {"code":0,"msg":"","data":{"minute":3,"silver":30,"time_start":1509638833,"time_end":1509639013,"times":1,"max_times":3}}
        if r:
            cur = time.time()
            if r['code'] == -10017:
                self.write({'free_sliver': False})
            elif r['data']['time_end'] < cur:
                self.get_free_silver(r['data'])
            else:
                self.write({'next_free_sliver_time': int(r['data']['time_end'])})

    def download_captcha(self):
        t = int(time.time() * 1000)
        params = {'ts': t}
        r = self.request(CAPTCHA_URL, 'GET', params=params)
        img_buf = StringIO.StringIO(r.content)  # 采用StringIO直接将验证码文件写到内存，省去写入硬盘
        img = Image.open(img_buf)  # PIL库加载图片
        return img

    def get_free_silver(self, data):
        img = self.download_captcha()
        captcha = ocr.recognize(img)
        params = {
            'time_start': data['time_start'],
            'end_time': data['time_end'],
            'captcha': captcha
        }
        r = self.request(GET_FREE_SILVER, 'GET', params=params)
        if r['code'] == 0:
            self.write({'silver_seed': self.silver_seed + int(r['data']['awardSilver'])})
        elif r['code'] == -800:
            self.write({'phone_verification': False})

    @api.multi
    def join_small_tv(self, room_id, tv_id):
        params = {
            'roomid': room_id,
            'raffleId': tv_id,
            '_': int(time.time() * 100)
        }
        pool = gevent.pool.Pool(len(self))
        for each_record in self:
            pool.add(gevent.spawn(each_record._join_small_tv, params=params))
        pool.join()

    def _join_small_tv(self, params):
        self.request(TV_URL, 'GET', params=params)
        self.env['bili_live_tools.raffle'].join_raffle(self.id, params['roomid'], params['raffleId'])

    @api.multi
    def join_raffle(self, room_id):
        params = {
            'roomid': room_id,
        }
        pool = gevent.pool.Pool(len(self))
        for each_record in self:
            pool.add(gevent.spawn(each_record._join_raffle, params=params))
        pool.join()

    def _join_raffle(self, params):
        r = self.request(QUERY_RAFFLE_URL, 'GET', params=params)
        if r:
            for d in r['data']:
                params['raffleId'] = d['raffleId']
                headers = {
                    'Host': 'api.live.bilibili.com',
                    'Origin': 'http://live.bilibili.com',
                    'Referer': 'http://live.bilibili.com/%s' % params['roomid'],
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0'
                }
                r = self.request(RAFFLE_URL, 'GET', params=params, headers=headers)
                if r:
                    self.env['bili_live_tools.raffle'].join_raffle(self.id, params['roomid'], params['raffleId'])

    def clean_gift_wizard(self):
        context = self._context.copy()
        context['clean_gift'] = 1
        context['active_ids'] = self.ids
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

    @api.multi
    def clean_gift(self, room_id):
        for each_record in self:
            if each_record.account_gift_ids:
                room_info = get_room_info(room_id=room_id)
                if room_info:
                    room_id, room_uid = room_info['room_id'], room_info['uid']
                    for each_gift in each_record.account_gift_ids:
                        try:
                            result, msg = each_gift.send_gift(room_id, room_uid, each_gift.amount)
                            if result:
                                each_gift.write({'amount': 0})
                            else:
                                raise exceptions.ValidationError(msg)
                        except Exception as e:
                            pass
                        else:
                            self.env.cr.commit()
