# -*- coding: utf-8 -*-
{
    'name': "bili_live_tools",
    'application': True,
    'summary': """
        B站直播区用小工具""",

    'description': """
        B站直播区用小工具
    """,

    'author': "Gzp",
    'website': "http://github.com/a741424975game",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Bilibili',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'views/parent_menus.xml',
        'views/bili_live_tools_account_gift_views.xml',
        'views/bili_live_tools_account_views.xml',
        'views/bili_live_tools_gift_views.xml',
        'views/bili_live_tools_send_gift_wizard.xml',
        'views/bili_live_tools_raffle_views.xml'
    ],
}
