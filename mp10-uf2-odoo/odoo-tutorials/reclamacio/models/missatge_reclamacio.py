from odoo import models, fields

class ClaimMessage(models.Model):
    _name = 'customer.claim.message'
    _description = 'Customer Claim Message'

    claim_id = fields.Many2one('customer.claim', string='Claim', required=True)
    author_id = fields.Many2one('res.partner', string='Author', required=True)
    message = fields.Text(string='Message', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
