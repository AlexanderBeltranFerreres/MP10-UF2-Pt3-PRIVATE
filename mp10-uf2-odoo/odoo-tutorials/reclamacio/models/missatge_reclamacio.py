from odoo import models, fields

class MissatgeReclamacio(models.Model):
    _name = 'customer.claim.message'
    _description = 'Missatge del estat de reclamació al client'
    ##No canvio els noms dels camps per si acas ja estan definits a mail i fa cabum
    reclamacio_id = fields.Many2one('client.reclamacio', string='Reclamacio', required=True)
    author_id = fields.Many2one('res.partner', string='Author', required=True)
    message = fields.Text(string='Missatge', required=True)
    date = fields.Datetime(string='Data', default=fields.Datetime.now)
