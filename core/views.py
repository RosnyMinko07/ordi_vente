from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from .models import *
import secrets
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Vente
from .models import Categorie, Produit
from django.contrib.auth import authenticate, login
from decimal import Decimal
from .models import PanierItem
from django.views.decorators.csrf import csrf_exempt
from coinbase_commerce.client import Client
client = Client(api_key='4cf013f9-582e-40ec-9d0b-ce631cfdd064')
from django.core.serializers.json import DjangoJSONEncoder
import json







def connexion_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirection en fonction du rôle
            if user.role == 'admin':
                return redirect('dashboard_admin')
            elif user.role == 'vendeur':
                return redirect('dashboard_vendeur')
            else:  # Par défaut pour les acheteurs
                return redirect('dashboard_acheteur')
        else:
            # Gestion des erreurs d'authentification
            return render(request, 'auth/connexion.html', {'error': 'Identifiants invalides'})
    
    return render(request, 'auth/connexion.html')


def inscription(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        # Validation des données
        if not all([username, email, password, role]):
            messages.error(request, 'Tous les champs sont obligatoires')
            return redirect('inscription')

        if role not in ['acheteur', 'vendeur']:  # Bloque les rôles non autorisés
            messages.error(request, 'Rôle invalide')
            return redirect('inscription')

        if Utilisateur.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà')
            return redirect('inscription')

        try:
            user = Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            login(request, user)
            messages.success(request, 'Inscription réussie!')
            
            # Redirection en fonction du rôle
            if role == 'acheteur':
                return redirect('dashboard_acheteur')
            else:
                return redirect('dashboard_vendeur')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
            return redirect('inscription')
    
    return render(request, 'auth/inscription.html')

def deconnexion_view(request):
    logout(request)
    return redirect('accueil')

# Admin Views
@login_required
def dashboard_admin(request):

    taux_remplissage_commandes = 75  # Exemple: pourcentage de commandes traitées
    stock_eleve = 60  # Pourcentage de produits avec stock élevé
    stock_moyen = 25  # Pourcentage de produits avec stock moyen  
    stock_faible = 15  # Pourcentage de produits avec stock faible

    context = {
        'taux_remplissage_commandes': taux_remplissage_commandes,
        'stock_eleve': stock_eleve,
        'stock_moyen': stock_moyen,
        'stock_faible': stock_faible,
        # ... autres variables
    }

     # Données pour les graphiques
    dates_ventes = ['01/01', '02/01', '03/01']  # Exemple
    montants_ventes = [1000, 1500, 2000]        # Exemple
    
    # Convertir en JSON
    context = {
        'dates_ventes': json.dumps(dates_ventes, cls=DjangoJSONEncoder),
        'montants_ventes': json.dumps(montants_ventes),
        'categories_labels': json.dumps(['Cat1', 'Cat2', 'Cat3']),
        'categories_data': json.dumps([3000, 2000, 1500]),
        'revenu_7jours': json.dumps([500, 600, 700, 800, 900, 1000, 1100]),
        # ... autres variables
    }
    if request.user.role != 'admin':
        return redirect('accueil')
    
    stats = {
        'ventes_total': Vente.objects.aggregate(Sum('prix_total'))['prix_total__sum'] or 0,
        'vendeurs_count': Utilisateur.objects.filter(role='vendeur').count(),
        'produits_count': Produit.objects.count()
    }
    
    return render(request, 'admin/dashboard.html', {'stats': stats})


@login_required
def historique_ventes_admin(request):
    ventes = Vente.objects.select_related('acheteur', 'vendeur').order_by('-date_vente')
    return render(request, 'admin/historique_ventes.html', {'ventes': ventes})

# Vendeur Views
@login_required
def dashboard_vendeur(request):
    if request.user.role != 'vendeur':
        return redirect('accueil')
    
    produits = Produit.objects.filter(vendeur=request.user)
    ventes = Vente.objects.filter(vendeur=request.user)
    
    context = {
        'produits_count': produits.count(),
        'ventes_total': ventes.aggregate(Sum('prix_total'))['prix_total__sum'] or 0,  # Correction ici
        'produits': produits.order_by('-date_creation')[:5]
    }
    return render(request, 'vendeur/dashboard.html', context)


def liste_vendeurs(request):
    vendeurs = Utilisateur.objects.filter(role='vendeur')  # Filtrer par rôle 'vendeur'
    return render(request, 'admin/vendeur/liste.html', {'vendeurs': vendeurs})


@login_required
def ajouter_produit(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        categorie_id = request.POST.get('categorie')
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        stock = request.POST.get('stock')
        image = request.FILES.get('image')

        # Validation des données
        if not categorie_id or not nom or not description or not prix or not stock or not image:
            messages.error(request, 'Tous les champs doivent être remplis.')
            return redirect('ajouter_produit')

        # Créer le produit
        try:
            produit = Produit.objects.create(
                vendeur=request.user,
                categorie_id=categorie_id,
                nom=nom,
                description=description,
                prix=prix,
                stock=stock,
                image=image
            )
            messages.success(request, 'Produit ajouté avec succès.')
            return redirect('liste_produits')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du produit : {str(e)}')
            return redirect('ajouter_produit')

    # Récupérer toutes les catégories pour le formulaire
    categories = Categorie.objects.all()
    return render(request, 'vendeur/produits/ajouter.html', {'categories': categories})


# Acheteur Views
def accueil(request):
    produits = Produit.objects.filter(est_actif=True)
    if 'q' in request.GET:
        produits = produits.filter(
            Q(nom__icontains=request.GET['q']) | 
            Q(description__icontains=request.GET['q'])
        )
    return render(request, 'accueil.html', {'produits': produits})

@login_required
def dashboard_acheteur(request):
    produits = Produit.objects.filter(est_actif=True)
    categories = Categorie.objects.all()
    
    # Filtres
    categorie_id = request.GET.get('categorie')
    recherche = request.GET.get('q')
    
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    if recherche:
        produits = produits.filter(
            Q(nom__icontains=recherche) |
            Q(description__icontains=recherche)
        )
    
    return render(request, 'acheteur/dashboard.html', {
        'produits': produits,
        'categories': categories,
        'selected_categorie': int(categorie_id) if categorie_id else None,
        'recherche': recherche or ''
    })

@login_required
def voir_panier(request):
    panier_items = PanierItem.objects.filter(utilisateur=request.user)
    total = sum(item.total for item in panier_items)

    panier = []
    for item in panier_items:
        panier.append({
            'id': item.id,
            'produit': item.produit,
            'quantite': item.quantite,
            'total': item.total,
            'type_produit': item.produit.__class__._meta.verbose_name.title()  # 👈 ici
        })

    return render(request, 'acheteur/panier.html', {
        'panier': panier,
        'total': total
    })

@login_required
def valider_commande(request):
    panier_items = PanierItem.objects.filter(utilisateur=request.user)
    if not panier_items.exists():
        return redirect('panier')
    
    # Création commande
    commande = Commande.objects.create(
        utilisateur=request.user,
        reference=secrets.token_hex(8).upper(),
        mode_paiement='crypto'
    )
    
    # Ajout des articles
    for item in panier_items:
        LigneCommande.objects.create(
            commande=commande,
            produit=item.produit,
            quantite=item.quantite,
            prix_unitaire=item.produit.prix
        )
        # Mise à jour stock
        item.produit.stock -= item.quantite
        item.produit.save()
    
    # Paiement Coinbase
    charge = create_coinbase_charge(commande)
    if charge:
        commande.coinbase_id = charge.id
        commande.save()
        panier_items.delete()
        return redirect(charge.hosted_url)
    
    commande.delete()
    messages.error(request, "Erreur lors du paiement")
    return redirect('panier')


@csrf_exempt
def webhook_coinbase(request):
    payload = request.body
    sig_header = request.headers.get('X-Cc-Webhook-Signature')

    try:
        event = Webhook.construct_event(
            payload,
            sig_header,
            settings.COINBASE_WEBHOOK_SECRET
        )
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return HttpResponse(status=400)

    if event.type == 'charge:confirmed':
        commande = Commande.objects.get(coinbase_id=event.data['id'])
        commande.statut = 'payee'
        commande.save()
        
        payment = event.data['payments'][0]
        TransactionCrypto.objects.create(
            commande=commande,
            crypto=payment['value']['crypto']['currency'],
            montant=payment['value']['crypto']['amount'],
            adresse_reception=payment['value']['crypto']['address'],
            tx_hash=payment['value']['crypto']['transaction_id']
        )

    return HttpResponse(status=200)

@login_required
def liste_produits(request):
    if request.user.role != 'vendeur':
        return redirect('accueil')
    
    produits = Produit.objects.filter(vendeur=request.user)
    
    # Filtre par statut
    statut = request.GET.get('statut')
    if statut == 'actif':
        produits = produits.filter(est_actif=True)
    elif statut == 'inactif':
        produits = produits.filter(est_actif=False)
    
    # Filtre par catégorie
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    
    categories = Categorie.objects.all()
    
    return render(request, 'vendeur/produits/liste.html', {
        'produits': produits,
        'categories': categories,
        'selected_categorie': int(categorie_id) if categorie_id else None,
        'statut_filter': statut
    })

@login_required
def historique_ventes_vendeur(request):
    if not request.user.is_authenticated or request.user.role != 'vendeur':
        return redirect('accueil')

    ventes = Vente.objects.filter(
        vendeur=request.user
    ).select_related('acheteur').order_by('-date_vente')  # ✅ retiré 'produit'

    # Filtrage par période
    periode = request.GET.get('periode')
    if periode == 'mois':
        ventes = ventes.filter(date_vente__month=timezone.now().month)
    elif periode == 'semaine':
        ventes = ventes.filter(date_vente__gte=timezone.now() - timezone.timedelta(days=7))

    # Calcul du total
    total_ventes = ventes.aggregate(total=Sum('prix_total'))['total'] or 0

    return render(request, 'vendeur/historique_ventes.html', {
        'ventes': ventes,
        'total_ventes': total_ventes,
        'periode': periode
    })


def detail_produit(request, pk):
    produit = get_object_or_404(
        Produit, 
        pk=pk, 
        est_actif=True
    )
    
    # Produits similaires (même catégorie)
    produits_similaires = Produit.objects.filter(
        categorie=produit.categorie,
        est_actif=True
    ).exclude(pk=pk)[:4]
    
    # Gestion du panier
    dans_le_panier = False
    if request.user.is_authenticated:
        dans_le_panier = PanierItem.objects.filter(
            utilisateur=request.user,
            produit=produit
        ).exists()
    
    return render(request, 'acheteur/produit/detail.html', {
        'produit': produit,
        'produits_similaires': produits_similaires,
        'dans_le_panier': dans_le_panier,
        'crypto_prices': produit.crypto_prices
    })


@login_required
def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, pk=produit_id, est_actif=True)

    if request.method == 'POST':
        quantite = int(request.POST.get('quantite', 1))

        # Vérification du stock
        if quantite > produit.stock:
            messages.error(request, "Quantité demandée non disponible")
            return redirect('detail_produit', pk=produit_id)

        # Ajout ou mise à jour du panier
        panier_item, created = PanierItem.objects.get_or_create(
            utilisateur=request.user,
            produit=produit,
            defaults={'quantite': quantite}
        )

        if not created:
            panier_item.quantite += quantite
            panier_item.save()

        messages.success(request, f"{produit.nom} ajouté à votre panier")
        return redirect('panier')

    return redirect('detail_produit', pk=produit_id)


def ajouter_vendeur(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        if username and email and mot_de_passe:
            utilisateur = Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=mot_de_passe,
                role='vendeur'
            )
            messages.success(request, 'Vendeur ajouté avec succès.')
            return redirect('liste_vendeurs')
        else:
            messages.error(request, 'Tous les champs sont obligatoires.')
    
    return render(request, 'admin/vendeur/ajouter.html')

def modifier_vendeur(request, vendeur_id):
    vendeur = get_object_or_404(Utilisateur, id=vendeur_id, role='vendeur')

    if request.method == 'POST':
        vendeur.username = request.POST.get('username')
        vendeur.email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        if mot_de_passe:
            vendeur.set_password(mot_de_passe)
        
        vendeur.save()
        messages.success(request, 'Vendeur modifié avec succès.')
        return redirect('liste_vendeurs')

    return render(request, 'admin/vendeur/modifier.html', {'vendeur': vendeur})


def supprimer_vendeur(request, vendeur_id):
    vendeur = get_object_or_404(Utilisateur, id=vendeur_id, role='vendeur')
    
    if request.method == 'POST':
        vendeur.delete()
        messages.success(request, 'Vendeur supprimé avec succès.')
        return redirect('liste_vendeurs')

    return render(request, 'admin/vendeur/supprimer.html', {'vendeur': vendeur})

def ajouter_categorie(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')

        if nom:
            Categorie.objects.create(nom=nom)
            messages.success(request, 'Catégorie ajoutée avec succès.')
            return redirect('liste_categories')
        else:
            messages.error(request, 'Le nom de la catégorie est obligatoire.')

    return render(request, 'admin/categories/ajouter.html')


def modifier_categorie(request, categorie_id):
    categorie = get_object_or_404(Categorie, id=categorie_id)

    if request.method == 'POST':
        categorie.nom = request.POST.get('nom')
        categorie.save()
        messages.success(request, 'Catégorie modifiée avec succès.')
        return redirect('liste_categories')

    return render(request, 'admin/categories/modifier.html', {'categorie': categorie})


def supprimer_categorie(request, categorie_id):
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, 'Catégorie supprimée avec succès.')
        return redirect('liste_categories')

    return render(request, 'admin/categories/supprimer.html', {'categorie': categorie})


# Vue pour afficher la liste des catégories
def liste_categories(request):
    categories = Categorie.objects.all()
    return render(request, 'admin/categories/liste.html', {'categories': categories})


def modifier_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, vendeur=request.user)

    if request.method == 'POST':
        # Récupération des données du formulaire
        categorie_id = request.POST.get('categorie')
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        stock = request.POST.get('stock')
        image = request.FILES.get('image')

        # Vérification
        if not categorie_id or not nom or not description or not prix or not stock:
            messages.error(request, 'Tous les champs doivent être remplis.')
            return redirect('modifier_produit', produit_id=produit.id)

        try:
            produit.categorie_id = categorie_id
            produit.nom = nom
            produit.description = description
            produit.prix = prix
            produit.stock = stock

            if image:
                produit.image = image  # Met à jour l’image uniquement si elle est modifiée

            produit.save()
            messages.success(request, 'Produit modifié avec succès.')
            return redirect('liste_produits')

        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('modifier_produit', produit_id=produit.id)

    categories = Categorie.objects.all()
    return render(request, 'vendeur/produits/modifier.html', {'produit': produit, 'categories': categories})

def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, vendeur=request.user)

    if request.method == 'POST':
        produit.delete()
        messages.success(request, 'Produit supprimé avec succès.')
        return redirect('liste_produits')

    return render(request, 'vendeur/produits/confirmation_suppression.html', {'produit': produit})






def afficher_panier(request):
    panier_session = request.session.get('panier', {})
    panier = []
    total = Decimal(0)

    for produit_id, item in panier_session.items():
        try:
            # Récupère le produit spécifique (ordinateur, téléphone, etc.)
            produit = Produit.objects.get(id=produit_id).get_real_instance()
            quantite = item['quantite']
            prix = Decimal(str(produit.prix))
            total_item = prix * quantite

            panier.append({
                'id': produit.id,
                'produit': produit,  # On utilise 'produit' au lieu de 'ordinateur'
                'quantite': quantite,
                'total': total_item
            })

            total += total_item
        except Produit.DoesNotExist:
            continue

    return render(request, 'acheteur/panier.html', {
        'panier': panier,
        'total': total
    })


def retirer_du_panier(request, item_id):
    item = get_object_or_404(PanierItem, id=item_id, utilisateur=request.user)
    item.delete()
    return redirect('voir_panier') 

def commande(request):
    panier = PanierItem.objects.filter(utilisateur=request.user)
    total = sum(item.total for item in panier)
    return render(request, 'acheteur/commande/confirmation.html', {'panier': panier, 'total': total})

def paiement(request):
    if request.method == 'POST':
        # 👉 Traitement du paiement ou redirection vers une passerelle
        return render(request, 'acheteur/commande/paiement.html')
    else:
        return redirect('commande')

@csrf_exempt
def crypto_paiement(request):
    utilisateur = request.user
    panier_items = PanierItem.objects.filter(utilisateur=utilisateur)

    # Calcul du total du panier en FCFA
    total_fcfa = sum(item.produit.prix * item.quantite for item in panier_items)

    # Conversion en USD
    taux_fcfa_usd = 600  # 1 USD = 600 FCFA
    total_usd = total_fcfa / taux_fcfa_usd

    # Conversion en BTC (optionnel)
    taux_btc_usd = 30000  # 1 BTC = 30 000 USD
    montant_btc = total_usd / taux_btc_usd

    # Initialisation du client Coinbase Commerce
    client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)

    # Création de la charge via l'objet client.charge
    charge_data = {
        'name': 'Paiement pour votre commande',
        'description': f'Commande totale de {total_fcfa} FCFA',
        'pricing_type': 'fixed_price',
        'local_price': {
            'amount': f'{total_usd:.2f}',
            'currency': 'USD'
        },
        'metadata': {
            'utilisateur_id': str(utilisateur.id)
        },
        'redirect_url': 'http://127.0.0.1:8000/paiement/confirmation/',
        'cancel_url': 'http://127.0.0.1:8000/panier/'
    }

    # ✅ LA BONNE MÉTHODE
    charge = client.charge.create(**charge_data)

    # Redirection vers Coinbase pour le paiement
    return redirect(charge.hosted_url)


def confirmation_paiement(request):
    # Créer un client Coinbase Commerce
    client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)

    # Vérifier la charge
    charge_id = request.GET.get('charge_id')
    charge = client.charges.retrieve(charge_id)

    if charge['status'] == 'COMPLETED':
        # Paiement réussi
        return render(request, 'acheteur/commande/paiement_valide.html', {
            'status': '🎉 Paiement réussi ! Merci pour votre commande.'
        })
    else:
        # Paiement échoué ou en attente
        return render(request, 'acheteur/commande/paiement_valide.html', {
            'status': '❌ Paiement échoué ou en attente. Veuillez réessayer.'
        })