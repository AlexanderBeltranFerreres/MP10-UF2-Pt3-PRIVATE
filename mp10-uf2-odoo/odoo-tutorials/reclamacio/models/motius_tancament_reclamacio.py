from odoo import models, fields

class MotiuTancamentReclamacio(models.Model):
    _name = 'client.reclamacio.tancament.motiu'
    _description = 'Motius de Tancament o Cancel·lació de Reclamacions'

    name = fields.Char('Motiu', required=True)
