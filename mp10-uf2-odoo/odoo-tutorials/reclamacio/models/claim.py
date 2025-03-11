from odoo import models, fields, api, validation_error

class Claim(models.Model):
    _name = 'customer.claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Claim'

    name = fields.Char(string='Subject', required=True)
    description = fields.Text(string='Initial Description', required=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='new', track_visibility='onchange')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Creation Date', default=fields.Datetime.now)
    write_date = fields.Datetime(string='Modification Date')
    close_date = fields.Datetime(string='Closure Date')
    messages = fields.One2many('customer.claim.message', 'claim_id', string='Messages')
    invoice_count = fields.Integer(string='Number of Invoices', compute='_compute_invoice_count')
    delivery_count = fields.Integer(string='Number of Deliveries', compute='_compute_delivery_count')
    resolution_description = fields.Text(string='Resolution Description')
    closure_reason_id = fields.Many2one('customer.claim.closure.reason', string='Closure Reason')

    @api.depends('sale_order_id')
    def _compute_invoice_count(self):
        for claim in self:
            claim.invoice_count = len(claim.sale_order_id.invoice_ids)

    @api.depends('sale_order_id')
    def _compute_delivery_count(self):
        for claim in self:
            claim.delivery_count = len(claim.sale_order_id.picking_ids)

    @api.constrains('sale_order_id', 'state')
    def _check_unique_open_claim(self):
        for claim in self:
            if claim.state in ['new', 'in_progress']:
                existing_claims = self.search([
                    ('sale_order_id', '=', claim.sale_order_id.id),
                    ('state', 'in', ['new', 'in_progress']),
                    ('id', '!=', claim.id)
                ])
                if existing_claims:
                    raise validation_error('There is already an open claim for this sales order.')

    def action_close(self):
        self.write({'state': 'closed', 'close_date': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reopen(self):
        self.write({'state': 'in_progress'})
