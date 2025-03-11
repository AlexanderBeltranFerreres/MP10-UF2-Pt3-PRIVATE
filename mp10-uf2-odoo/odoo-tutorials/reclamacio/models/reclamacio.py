from odoo import models, fields, api, validation_error

class Reclamacio(models.Model):
    _name = 'client.reclamacio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Reclamacio del Client'

    ##No canvio els noms dels camps per si acas ja estan definits a sales i fa cabum
    name = fields.Char(string='Tema', required=True)
    description = fields.Text(string='Descripcio', required=True)
    state = fields.Selection([
        ('new', 'Nova'),
        ('in_progress', 'En progrés'),
        ('closed', 'Tancada'),
        ('cancelled', 'Cancel·lada')
    ], string='Status', default='new', track_visibility='onchange')
    sale_order_id = fields.Many2one('sale.order', string='Ordre de Venta', required=True)
    customer_id = fields.Many2one('res.partner', string='Client', required=True)
    user_id = fields.Many2one('res.users', string='Creada per ', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Data de creacio', default=fields.Datetime.now)
    write_date = fields.Datetime(string='Data de modificacio')
    close_date = fields.Datetime(string='Data de tancament')
    messages = fields.One2many('customer.claim.message', 'reclamacio_id', string='Missatges')
    invoice_count = fields.Integer(string='Numero de factures', compute='_compute_total_factures')
    delivery_count = fields.Integer(string='Numero de entregues', compute='_compute_total_entregues')
    resolution_description = fields.Text(string='Descripció de resolució')
    closure_reason_id = fields.Many2one('client.reclamacio.tancament.motiu', string='Motiu de tancament')

    @api.depends('sale_order_id')
    #per a calcular les factures associades, _compute per a que odoo ho identifique sino pot donar problem
    def _compute_total_factures(self):
        for reclamacio in self:
            reclamacio.invoice_count = len(reclamacio.sale_order_id.invoice_ids)

    #per a calcular les entregues associades
    @api.depends('sale_order_id')
    def _compute_total_entregues(self):
        for reclamacio in self:
            reclamacio.delivery_count = len(reclamacio.sale_order_id.picking_ids)

    @api.constrains('sale_order_id', 'state')
    def _check_una_reclamacio_oberta(self):
        for reclamacio in self:
            if reclamacio.state in ['new', 'in_progress']:
                existeix_reclamacio = self.search([
                    ('sale_order_id', '=', reclamacio.sale_order_id.id),
                    ('state', 'in', ['new', 'in_progress']),
                    ('id', '!=', reclamacio.id)
                ])
                if existeix_reclamacio:
                    raise validation_error('Ja hi ha una reclamació oberta per a aquesta compra, sol pot haber 1 per ordre de compra.')

    def action_close(self):
        self.write({'state': 'closed', 'close_date': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reopen(self):
        self.write({'state': 'in_progress'})
