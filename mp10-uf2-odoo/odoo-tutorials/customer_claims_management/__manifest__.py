{
   "name": "Gestio Reclamacions",
   "version": "1.0",
   "summary": "Gestionar Reclamacions",
   "category": "Sales",
   "application": True,
   "depends": ["base","sale","mail"],
   "data": [
      "security/ir.model.access.csv",
      "views/claim_views.xml",
      "views/claim_message_views.xml",
      "views/claim_closure_reason_views.xml",
      "views/sale_order_views.xml",
      "data/claim_closure_reason_data.xml",
   ],
   "installable": True,
"license": "LGPL-3",
}