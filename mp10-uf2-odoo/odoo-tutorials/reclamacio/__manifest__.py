{
   "name": "Gestio Reclamacions",
   "version": "1.0",
   "summary": "Gestionar Reclamacions",
   "category": "Sales",
   "application": True,
   "depends": ["base","sale","mail"],
   "data": [
      "security/ir.model.access.csv",
      "views/reclamacio_views.xml",
      "views/missatge_reclamacio_views.xml",
      "views/motiu_tancament_reclamacio_views.xml",
      "views/ordres_ventes_views.xml",
      "data/motius_tancament_reclamacio_data.xml",
   ],
   "installable": True,
"license": "LGPL-3",
}