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

    # Afegir camp per a la comanda de vendes associada
    sale_order_id = fields.Many2one('sale.order', string="Comanda de Vendes", ondelete='set null')

    # Camps dels numero total de factures i els enviament de la comanda associada
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
    
    # Camps per a les factures associades a la comanda de venda
    invoice_ids = fields.One2many(
        'account.move', 
        'invoice_origin', 
        string="Factures", 
        domain=[('move_type', '=', 'out_invoice')],
        compute="_compute_invoice_ids", 
        store=False
    )
    # Camps per a enviaments associats a la comanda de venda
    picking_ids = fields.One2many(
        'stock.picking', 
        'origin', 
        string="Enviaments",
        compute="_compute_picking_ids", 
        store=False
    )
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
                # Comprovar si és un registre nou que no esta la base de dades
                if not record.id:
                    # Mirar si tenim una reclamacio (nova o en_tractament) pper a la comanda que hem associat
                    existing_reclamacio = self.search([
                        ('sale_order_id', '=', record.sale_order_id.id),
                        ('state', 'in', ['nova', 'en_tractament'])
                    ])
                    if existing_reclamacio:
                        raise ValidationError('Ja existeix una reclamació oberta per aquesta comanda de venda.')
                else:
                    # Si existix una reclamacio mirem que no s'estigui canviant l'estat a nova o en_tractament
                    existing_reclamacio = self.search([
                        ('sale_order_id', '=', record.sale_order_id.id),
                        ('state', 'in', ['nova', 'en_tractament']),
                        ('id', '!=', record.id)  # Traem el registre actuial
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
                    raise ValidationError('Els missatges no estan correctament associats a aquesta reclamació.')

                # Canviar l'estat a en tractament
                record.state = 'en_tractament'

                # Crear un missatge automàtic per indicar que s'ha posat en tractament
                self.env['client.reclamacio.message'].create({
                    'reclamacio_id': record.id,  # Mirem si el missatge està associat a la erclamacio
                    'message': 'Reclamació en tractament.',
                    'author_id': self.env.user.id,
                })
            else:
                raise ValidationError('Només es pot posar en tractament una reclamació nova.')

    def write(self, vals):
        # Comprovar si estem canviant l'estat
        if 'state' in vals:
            for record in self:
                    
                # Mirem si estem canviant l'estat a 'en_tractament'
                if vals['state'] == 'en_tractament':
                    # Mirem si te un missatge associat
                    if not record.message_ids:
                        raise ValidationError('Per posar la reclamació en tractament, s\'ha de crear almenys un missatge associat.')
                    
                    # Comprovar si els missatges estan associats correctament amb la reclamació
                    if any(message.reclamacio_id != record for message in record.message_ids):
                        raise ValidationError('Els missatges no estan correctament associats a aquesta reclamació.')

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
                record = self.browse(record_id)  # Obtenir el registre per l'ID

                # Log per comprovar TREURE DESPRES
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
                        'tag': 'reload',
                    }
                else:
                    _logger.error('El registre no és de odoo (basemodel)')
        else:
            _logger.error('Funcio buida')

        _logger.info('no fa res la funció')


    
    def action_cancelar_comanda(self):
        for record in self:
            if not record.sale_order_id:
                raise ValidationError('La reclamació no té cap comanda associada.')

            sale_order = record.sale_order_id

            # SI FACTURES PUBLICADES MISSATGE
            if any(invoice.state == 'posted' for invoice in sale_order.invoice_ids):
                raise ValidationError("No es pot cancel·lar la comanda ja que té factures publicades.")

            # Cancel·lar primer els enviaments pendents
            for picking in sale_order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                picking.button_cancel()

            # Cancel·lar les factures en esborrany (no publicades)
            for invoice in sale_order.invoice_ids.filtered(lambda i: i.state == 'draft'):
                invoice.button_cancel()


            # Enviar correu
            template = self.env.ref('reclamacio.correu_cancelar_ordre')
            if template:
                
                #Veure que passa exactament a la plantilla
                _logger.info(f"Valors passats a la plantilla:\n"
                            f"  - Comanda ID: {sale_order.id}\n"
                            f"  - Nom comanda: {sale_order.name}\n"
                            f"  - Client: {sale_order.partner_id.name}\n"
                            f"  - Email client: {sale_order.partner_id.email}")

                #Passar tots els valors manualment AL OBJECTE
                mail_context = {
                    'object': sale_order,
                    'sale_order_id': sale_order.id,
                    'sale_order_name': sale_order.name,
                    'partner_name': sale_order.partner_id.name,
                    'partner_email': sale_order.partner_id.email,
                }

                template.with_context(mail_context).send_mail(sale_order.id, force_send=True)
                
            # cancel·lem la comanda
            sale_order.write({'state': 'cancel'})
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
        
        ##Evitar error si no hi ha enviaments associats.
        
        if not self.picking_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        return self._get_action_view_picking(self.picking_ids)


    @api.depends('sale_order_id')
    def _compute_invoice_ids(self):
        for rec in self:
            if rec.sale_order_id:
                rec.invoice_ids = self.env['account.move'].search([
                    ('invoice_origin', '=', rec.sale_order_id.name),
                    ('move_type', '=', 'out_invoice')
                ])
            else:
                rec.invoice_ids = False

    @api.depends('sale_order_id')
    def _compute_picking_ids(self):
        for rec in self:
            if rec.sale_order_id:
                rec.picking_ids = self.env['stock.picking'].search([
                    ('origin', '=', rec.sale_order_id.name)
                ])
            else:
                rec.picking_ids = False



class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Afegir enllaç a reclamació
    reclamacio_id = fields.Many2one('client.reclamacio', string="Reclamació", ondelete='cascade')
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # enllaç reclamació
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

            # Cancel·lar els enviaments pendents
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                picking.button_cancel()

            # Cancel·lar les factures en esborrany (no publicades)
            for invoice in order.invoice_ids.filtered(lambda i: i.state == 'draft'):
                invoice.button_cancel()

            # Enviar correu
            template = self.env.ref('reclamacio.correu_cancelar_ordre')
            if template:
                template.send_mail(order.id, force_send=True)

            # cancel·lem la comanda
            return super(SaleOrder, self).action_cancel()

    def action_view_delivery(self):
        """
        Evitar error si no hi ha enviaments associats.
        """
        if not self.picking_ids:
            return {'type': 'ir.actions.act_window_close'}  # No fer res si no hi ha enviaments
        
        return self._get_action_view_picking(self.picking_ids)