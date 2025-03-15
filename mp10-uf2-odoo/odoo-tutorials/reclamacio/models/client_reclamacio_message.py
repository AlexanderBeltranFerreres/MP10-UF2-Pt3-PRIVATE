from odoo import models, fields, api
from odoo.exceptions import ValidationError
import inspect
import logging
_logger = logging.getLogger(__name__)

class ClientReclamacioMessage(models.Model):
    _name = 'client.reclamacio.message'

    message = fields.Text("Missatge")
    author_id = fields.Many2one('res.users', string="Autor")
    partner_id = fields.Many2one('res.partner', string="Client")
    message_date = fields.Datetime("Data del Missatge")
    reclamacio_id = fields.Many2one('client.reclamacio', string="Reclamació")
    reclamacio_name = fields.Char(related='reclamacio_id.name', string="Reclamació", store=True)

    @api.model
    def create(self, vals):
        vals['message_date'] = fields.Datetime.now()

        # Comprovar si l'autor és un client (no un usuari d'Odoo)
        partner_id = vals.get('partner_id')
        if partner_id:
            # Si el missatge ve d'un client, és obligatòria
            if not vals.get('reclamacio_id'):
                vals['reclamacio_id'] = False  # Potser no hi ha comanda associada
        else:
            # Si el missatge ve d'un usuari d'Odoo,obligatòria
            if not vals.get('reclamacio_id'):
                raise ValidationError('Per als missatges d\'usuari d\'Odoo, cal indicar una comanda associada.')

        return super(ClientReclamacioMessage, self).create(vals)


    @api.model
    def write(self):
        raise ValidationError("Els missatges no es poden modificar un cop creats.")
    
    def unlink(self):
        raise ValidationError("Els missatges no es poden esborrar.")

        