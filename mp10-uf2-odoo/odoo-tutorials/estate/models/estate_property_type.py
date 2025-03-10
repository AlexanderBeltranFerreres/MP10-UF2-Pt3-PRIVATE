from odoo import models, fields

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Tipus de propietat'

    name = fields.Char('Nom', required=True)