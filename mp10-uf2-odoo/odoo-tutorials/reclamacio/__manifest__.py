{
    'name': 'Customer Claims Management',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Manage customer claims efficiently',
    'depends': ['sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/claim_views.xml',
        'views/claim_message_views.xml',
        'views/claim_closure_reason_views.xml',
        'views/sale_order_views.xml',
        'data/claim_closure_reason_data.xml',
    ],
    'installable': True,
    'application': True,
}