from odoo import fields, models, tools
class ReportEstateNombreOfertesPerPropietat(models.Model):
    _name = 'report.nombre.ofertes.propietat'
    _description = "Module Report"

    _auto = False
    _rec_name = 'name'
    name = fields.Char(string='Propietat', readonly=True)
    nombre_ofertes = fields.Integer(string="Nombre d'ofertes", readonly=True)
    
    def _select(self):
        return """
        t.id as id,
        t.name as name,
        count(1) as nombre_ofertes
        """
    def _from(self):
        return """
        estate_property t
        LEFT JOIN estate_property_offer o ON t.id = o.property_id
        """
    def _group_by(self):
        return """
        t.id, t.name
        """
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(""" CREATE or REPLACE VIEW %s as
            SELECT %s
            FROM %s
            GROUP BY %s
            """ % (self._table, self._select(), self._from(), self._group_by())
        )