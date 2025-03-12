from odoo import models, fields

class ClientReclamacioMessage(models.Model):
    _name = 'client.reclamacio.message'

    message = fields.Text("Missatge")
    author_id = fields.Many2one('res.users', string="Autor")
    partner_id = fields.Many2one('res.partner', string="Client")
    message_date = fields.Datetime("Data del Missatge")
    reclamacio_id = fields.Many2one('client.reclamacio', string="Reclamació")