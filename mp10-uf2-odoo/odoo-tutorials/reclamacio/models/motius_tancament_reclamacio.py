from odoo import models, fields

class MotiuTancamentReclamacio(models.Model):
    _name = 'client.reclamacio.tancament.motiu'
    _description = 'Motiu de Tancament de Reclamacio al Client'

    name = fields.Char(string='Motiu', required=True)
