{
   'name': 'Gestio Reclamacions',
   'version': '3.2',
   'summary': 'Gestionar Reclamacions',
   'author': 'David Groza & Alexander Beltran',
   'category': 'Sales',
   'application': True,
   'depends': ['base','sale'],
   'data': [
      'security/ir.model.access.csv',
      'views/reclamacio_views.xml',
      'views/reclamacio_menus.xml',
      'data/motius_tancament_reclamacio_data.xml',
   ],
   'installable': True,
}