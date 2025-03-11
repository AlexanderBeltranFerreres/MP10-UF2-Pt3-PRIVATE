from odoo import models, fields

class ClaimClosureReason(models.Model):
    _name = 'customer.claim.closure.reason'
    _description = 'Customer Claim Closure Reason'

    name = fields.Char(string='Reason', required=True)
