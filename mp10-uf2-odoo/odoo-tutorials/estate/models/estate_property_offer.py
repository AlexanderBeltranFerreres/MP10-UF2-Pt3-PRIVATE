from odoo import models, fields

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Ofertes de propietat'

    price = fields.Float('Preu Oferit', required=True)
    state = fields.Selection(
        [
            ('accepted', 'Acceptada'),
            ('rejected', 'Cancel·lada'),
            ('pending', 'Pendent')
        ], 
        default='pending', string="Estat"
    )
    buyer_id = fields.Many2one('res.partner', string="Comprador")
    comments = fields.Text('Comentaris')
    property_id = fields.Many2one('estate.property', string="Propietat", readonly=True)

    def action_accept(self):
        self.ensure_one()
        self.state = 'accepted'
        self.property_id.final_price = self.price
        self.property_id.buyer_id = self.buyer_id
        self.property_id.state = 'offer_accepted'

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
        
        other_accepted_offer = self.property_id.offer_ids.filtered(lambda o: o.state == 'accepted' and o.id != self.id)
        
        if self.property_id.final_price == self.price:
            if other_accepted_offer:
                self.property_id.final_price = other_accepted_offer[0].price
                self.property_id.buyer_id = other_accepted_offer[0].buyer_id
            else:
                self.property_id.final_price = 0
                self.property_id.buyer_id = False
                self.property_id.state = 'new'
