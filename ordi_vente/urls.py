from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import *

urlpatterns = [

    
    # Auth
    path('connexion/', connexion_view, name='connexion'),
    path('inscription/', inscription, name='inscription'),
    path('deconnexion/', deconnexion_view, name='deconnexion'),
    
    # Public
    path('', accueil, name='accueil'),
    
    # Admin
    path('admin/dashboard/', dashboard_admin, name='dashboard_admin'),
    path('admin/historique/', historique_ventes_admin, name='historique_ventes_admin'),
    path('admin/vendeurs/', liste_vendeurs, name='liste_vendeurs'),
    path('admin/vendeurs/ajouter/', ajouter_vendeur, name='ajouter_vendeur'),
    path('admin/vendeurs/modifier/<int:vendeur_id>/', modifier_vendeur, name='modifier_vendeur'),
    path('admin/vendeurs/supprimer/<int:vendeur_id>/', supprimer_vendeur, name='supprimer_vendeur'),
    path('admin/categorie/ajouter/', ajouter_categorie, name='ajouter_categorie'),
    path('admin/categorie/modifier/<int:id>/', modifier_categorie, name='modifier_categorie'),
    path('supprimer/<int:id>/', supprimer_categorie, name='supprimer_categorie'),
    path('admin/categories/', liste_categories, name='liste_categories'),

    # Vendeur
    path('vendeur/dashboard/', dashboard_vendeur, name='dashboard_vendeur'),
    path('vendeur/produits/ajouter/', ajouter_produit, name='ajouter_produit'),
    path('vendeur/produits/', liste_produits, name='liste_produits'),
    path('vendeur/historique/', historique_ventes_vendeur, name='historique_ventes_vendeur'),
    path('produits/modifier/<int:produit_id>/', modifier_produit, name='modifier_produit'),
    path('produits/supprimer/<int:produit_id>/', supprimer_produit, name='supprimer_produit'),


    
    # Acheteur
    path('acheteur/dashboard/', dashboard_acheteur, name='dashboard_acheteur'),
    path('produit/<int:pk>/', detail_produit, name='detail_produit'),
    path('panier/', voir_panier, name='voir_panier'),
    path('panier/ajouter/<int:produit_id>/', ajouter_au_panier, name='ajouter_au_panier'),
    path('commande/valider/', valider_commande, name='valider_commande'),
    path('panier/', afficher_panier, name='panier'),
    path('retirer-du-panier/<int:item_id>/', retirer_du_panier, name='retirer_du_panier'),
    path('commande/', commande, name='commande'),
    path('paiement/', paiement, name='paiement'),
    path('paiement/crypto/', crypto_paiement, name='crypto_paiement'),
    path('crypto/', crypto_paiement, name='crypto_paiement'),
    path('confirmation-crypto/', confirmation_paiement, name='confirmation_crypto'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)