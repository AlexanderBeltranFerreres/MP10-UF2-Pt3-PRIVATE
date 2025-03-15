from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

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

    # Afegir camp per a la comanda de vendes
    sale_order_id = fields.Many2one('sale.order', string="Comanda de Vendes", ondelete='set null')

    # Camps amb el total de factures i els enviament associats al comanda
    invoice_count = fields.Integer(
        string="Nombre de Factures",
        compute="_compute_invoice_count",
        store=True
    )

    delivery_count = fields.Integer(
        string="Nombre d'Enviaments",
        compute="_compute_delivery_count",
        store=True
    )
    
    # Afegir camps per a les factures associades
    invoice_ids = fields.One2many('account.move', 'reclamacio_id', string="Factures", domain=[('move_type', '=', 'out_invoice')])
    
    # Afegir camps per a enviaments associats
    picking_ids = fields.One2many('stock.picking', 'reclamacio_id', string="Enviaments")

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

    @api.constrains('sale_order_id', 'state')
    def _check_unique_open_reclamacio(self):
        for record in self:
            if record.state in ['nova', 'en_tractament']:
                # Comprovar si és un registre nou (no guardat a la base de dades)
                if not record.id:  # Si no té id, vol dir que és nou
                    # Cercar si ja existeix una reclamació oberta (nova o en_tractament) per la mateixa comanda
                    existing_reclamacio = self.search([
                        ('sale_order_id', '=', record.sale_order_id.id),
                        ('state', 'in', ['nova', 'en_tractament'])
                    ])
                    if existing_reclamacio:
                        raise ValidationError('Ja existeix una reclamació oberta per aquesta comanda de venda.')
                else:
                    # Si ja és un registre existent, comprovem que no s'estigui canviant l'estat a nova o en_tractament
                    existing_reclamacio = self.search([
                        ('sale_order_id', '=', record.sale_order_id.id),
                        ('state', 'in', ['nova', 'en_tractament']),
                        ('id', '!=', record.id)  # Excloem el registre actual
                    ])
                    if existing_reclamacio:
                        raise ValidationError('Ja existeix una reclamació oberta per aquesta comanda de venda.')

    
    @api.model
    def action_en_tractament(self):
        for record in self:
            # Comprovar que l'estat actual sigui 'nova' abans de canviar a 'en_tractament'
            if record.state == 'nova':
                # Comprovar si hi ha almenys un missatge associat
                if not record.message_ids:
                    raise ValidationError('Per posar la reclamació en tractament, s\'ha de crear almenys un missatge associat.')

                # Comprovar si el missatge està associat correctament amb la reclamació
                if any(message.reclamacio_id != record for message in record.message_ids):
                    raise ValidationError('Els missatges associats no estan correctament vinculats a aquesta reclamació.')

                # Canviar l'estat a en tractament
                record.state = 'en_tractament'

                # Crear un missatge automàtic per indicar que s'ha posat en tractament
                self.env['client.reclamacio.message'].create({
                    'reclamacio_id': record.id,  # Assegurar-se que el missatge estigui associat a la reclamació
                    'message': 'Reclamació en tractament.',
                    'author_id': self.env.user.id,
                })
            else:
                raise ValidationError('Només es pot posar en tractament una reclamació nova.')

    def write(self, vals):
        # Comprovar si estem canviant l'estat
        if 'state' in vals:
            for record in self:
                # Si estem reobrint la reclamació, assegurem-nos que l'estat actual sigui 'tancada'
                if vals['state'] == 'en_tractament' and record.state != 'tancada':
                    raise ValidationError('Només es poden reobrir reclamacions tancades.')
                    
                # Validació si estem canviant l'estat a 'en_tractament'
                if vals['state'] == 'en_tractament':
                    # Comprovar si hi ha almenys un missatge associat
                    if not record.message_ids:
                        raise ValidationError('Per posar la reclamació en tractament, s\'ha de crear almenys un missatge associat.')
                    
                    # Comprovar si els missatges estan associats correctament amb la reclamació
                    if any(message.reclamacio_id != record for message in record.message_ids):
                        raise ValidationError('Els missatges associats no estan correctament vinculats a aquesta reclamació.')

        return super(ClientReclamacio, self).write(vals)


    @api.model
    def action_tancar(self):
        for record in self:
            if record.state != 'en_tractament':
                raise ValidationError('Només es poden tancar reclamacions en tractament.')
            record.state = 'tancada'
            record.close_date = fields.Datetime.now()

    @api.model
    def action_cancelar(self, reason_id):
        for record in self:
            if record.state == 'tancada':
                raise ValidationError('No es pot cancel·lar una reclamació tancada.')
            record.state = 'cancel·lada'
            record.cancel_reason_id = reason_id

    @api.model
    def action_reobrir(self, *args):
        _logger.info('self: %s', self)
        _logger.info('args: %s', args)

        if args:
            ##ITERAR SOBER ARGS PERQUE ÉS EL QUE PASSA ODOO NOU NO EL QUE TENIM, SINO DONA ERROR
            for record_id in args[0]:  # args[0] conté la llista d'IDs
                record = self.browse(record_id)  # Obtenir el registre complet per l'ID

                # Log per veure el que estem processant
                _logger.info('Processant registre: %s', record)
                if isinstance(record, models.BaseModel):  # Verifiquem que és un registre de Odoo
                    _logger.info('Registre és una instància de BaseModel')
                    if record.state != 'tancada':
                        _logger.error('El registre no està tancat, no es pot reobrir.')
                        raise ValidationError('Només es poden reobrir reclamacions tancades.')
                    
                    # Canviar l'estat a nova pq si fiquem a en_tractament diu que necessitem un missatge i esborrar la data de tancament
                    record.state = 'nova'
                    record.close_date = False  # Esborrem la data de tancament
                    _logger.info('Canviat l\'estat a "nova" i esborrada la data de tancament')

                    # Enviar una acció per refrescar la vista
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',  # Asegura't que es refresqui la vista
                    }
                else:
                    _logger.error('El registre no és una instància de BaseModel.')
        else:
            _logger.error('No s\'han passat arguments a la funció.')

        _logger.info('Funció acabada sense processar cap registre.')



    
    def action_cancelar_comanda(self, *args):
        for record in self:
            if not record.sale_order_id:
                raise ValidationError('Aquesta reclamació no té cap comanda associada.')
            
            # Comprovem si la comanda ja té factures publicades
            if any(invoice.state == 'posted' for invoice in record.sale_order_id.invoice_ids):
                raise ValidationError("No es pot cancel·lar la comanda ja que té factures publicades.")
            
            # Comprovem que la comanda no estigui en estat 'sale' o 'done'
            if record.sale_order_id.state in ['sale', 'done']:
                raise ValidationError('No es pot cancel·lar una comanda de venda confirmada o finalitzada.')
            
            # Cancel·lem els enviaments no realitzats
            for picking in record.sale_order_id.picking_ids.filtered(lambda p: p.state != 'done'):
                picking.action_cancel()
            
            # Cancel·lem les factures no publicades
            for invoice in record.sale_order_id.invoice_ids.filtered(lambda i: i.state != 'posted'):
                invoice.button_cancel()

            # Enviar correu al client informant de la cancel·lació
            template = self.env.ref('reclamacio.correu_cancelar_ordre')
            template.send_mail(record.sale_order_id.id, force_send=True)

            # Finalment, cancel·lem la comanda
            record.sale_order_id.action_cancel()  # Cancel·la la comanda
            

        return True

    @api.depends('sale_order_id')
    def _compute_invoice_count(self):
        for rec in self:
            if rec.sale_order_id:
                rec.invoice_count = self.env['account.move'].search_count([
                    ('invoice_origin', '=', rec.sale_order_id.name),
                    ('move_type', '=', 'out_invoice')
                ])
            else:
                rec.invoice_count = 0

    @api.depends('sale_order_id')
    def _compute_delivery_count(self):
        for rec in self:
            if rec.sale_order_id:
                rec.delivery_count = self.env['stock.picking'].search_count([
                    ('origin', '=', rec.sale_order_id.name)
                ])
            else:
                rec.delivery_count = 0

    def action_view_delivery(self):
        """
        Evitar error si no hi ha enviaments associats.
        """
        if not self.picking_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        return self._get_action_view_picking(self.picking_ids)





class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Afegir el vincle amb la reclamació
    reclamacio_id = fields.Many2one('client.reclamacio', string="Reclamació", ondelete='cascade')
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # Afegir el vincle amb la reclamació
    reclamacio_id = fields.Many2one('client.reclamacio', string="Reclamació", ondelete='cascade')


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    claim_ids = fields.One2many('client.reclamacio', 'sale_order_id', string="Reclamacions")
    invoice_count = fields.Integer(string="Nombre de Factures", compute="_compute_invoice_count", store=True)
    delivery_count = fields.Integer(string="Nombre d'Enviaments", compute="_compute_delivery_count", store=True)
    picking_ids = fields.One2many('stock.picking', 'reclamacio_id', string="Enviaments")
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)
    
    @api.depends('picking_ids')
    def _compute_delivery_count(self):
        for order in self:
            order.delivery_count = len(self.env['stock.picking'].search([('origin', '=', order.name)]))
    
    def action_cancel(self):
        for order in self:
            if any(invoice.state == 'posted' for invoice in order.invoice_ids):
                raise ValidationError("No es pot cancel·lar la comanda ja que té factures publicades.")
            
            # Enviar correu al client informant de la cancel·lació
            template = self.env.ref('reclamacio.correu_cancelar_ordre')
            template.send_mail(order.id, force_send=True)
            
            # Cancel·lar la comanda i les factures associades no publicades
            # Primer, cancel·lem els enviaments que no han estat realitzats
            for picking in order.picking_ids.filtered(lambda p: p.state != 'done'):
                picking.action_cancel()

            # Després, cancel·lem les factures no publicades
            for invoice in order.invoice_ids.filtered(lambda i: i.state != 'posted'):
                invoice.button_cancel()
            
            # Finalment, cancel·lem la comanda
            return super(SaleOrder, self).action_cancel()

    def action_view_delivery(self):
        """
        Evitar error si no hi ha enviaments associats.
        """
        if not self.picking_ids:
            return {'type': 'ir.actions.act_window_close'}  # No fer res si no hi ha enviaments
        
        return self._get_action_view_picking(self.picking_ids)