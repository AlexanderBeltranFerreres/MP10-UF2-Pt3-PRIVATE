from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ClientReclamacio(models.Model):
    _name = 'client.reclamacio'
    _description = 'Reclamacions dels clients'

    # Assumpte de la reclamació
    name = fields.Char('Assumpte de la Reclamació', required=True)

    # Descripció inicial de la reclamació
    description = fields.Text('Descripció Inicial')

    # Estat de la reclamació
    state = fields.Selection([
        ('nova', 'Nova'),
        ('en_tractament', 'En Tractament'),
        ('tancada', 'Tancada'),
        ('cancel·lada', 'Cancel·lada'),
    ], string='Estat', default='nova', required=True)

    # Comanda de vendes associada
    sale_order_id = fields.Many2one('sale.order', string='Comanda de Vendes')

    # Client que fa la reclamació
    partner_id = fields.Many2one('res.partner', string='Client', required=True)

    # Usuari que crea la reclamació
    user_id = fields.Many2one('res.users', string='Usuari Creador', default=lambda self: self.env.user)

    # Dates
    create_date = fields.Datetime('Data de Creació', default=fields.Datetime.now)
    write_date = fields.Datetime('Data de Modificació', default=fields.Datetime.now)
    close_date = fields.Datetime('Data de Tancament')

    # Missatges associats a la reclamació
    message_ids = fields.One2many('client.reclamacio.message', 'reclamacio_id', string='Missatges')

    # Descripció de la resolució final
    resolution_description = fields.Text('Descripció de la Resolució Final')

    # Motiu de tancament o cancel·lació
    cancel_reason_id = fields.Many2one('client.reclamacio.tancament.motiu', string='Motiu de Tancament o Cancel·lació')
