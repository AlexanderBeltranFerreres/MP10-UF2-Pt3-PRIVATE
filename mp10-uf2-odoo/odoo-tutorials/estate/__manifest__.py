{
   "name": "Estate",
   "version": "1.0",
   "summary": "Manage estate properties",
   "category": "Real Estate",
   "application": True,
   "depends": ["base"],
   "data": [
      "security/ir.model.access.csv",
      "views/estate_property_views.xml",
      "views/estate_menus.xml",
      "report/estate_property_reports.xml",
      "report/estate_property_templates.xml"
   ],
   "installable": True,
   "license": "LGPL-3",
}