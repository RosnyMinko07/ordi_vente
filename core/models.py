from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import json
default=timezone.now() 
from django.contrib.auth import get_user_model
from django.utils.text import slugify


class Utilisateur(AbstractUser):
    ROLES = (
        ('admin', 'Administrateur'),
        ('vendeur', 'Vendeur'),
        ('acheteur', 'Acheteur'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='acheteur')
    est_actif = models.BooleanField(default=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    wallet_crypto = models.CharField(max_length=100, blank=True)
    date_inscription = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)  # Le slug est maintenant généré automatiquement
    icone = models.CharField(max_length=50, default='bi-laptop')
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def save(self, *args, **kwargs):
        # Génération automatique du slug
        if not self.slug:
            self.slug = slugify(self.nom)

        # Gestion des collisions de slug
        original_slug = self.slug
        counter = 1
        while Categorie.objects.filter(slug=self.slug).exists():
            self.slug = f'{original_slug}-{counter}'
            counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom
    


class Vente(models.Model):  # Ligne 211
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ventes_effectuees')  # Ligne 212
    acheteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achats', null=True, blank=True)  # Nouveau champ
    produit = models.CharField(max_length=100)
    quantite = models.PositiveIntegerField()
    date_vente = models.DateTimeField(auto_now_add=True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Vente #{self.id} - {self.produit} par {self.vendeur.username}"

class Produit(models.Model):
    ETAT_CHOICES = (
        ('neuf', 'Neuf'),
        ('occasion', 'Occasion'),
        ('reconditionne', 'Reconditionné'),
    )
    
    vendeur = models.ForeignKey(
        'Utilisateur',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'vendeur'},
        related_name='produits_vendus'
    )
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.PROTECT,
        related_name='produits'
    )
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    etat = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default='neuf'
    )
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='produits/%Y/%m/')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Supprimé la conversion en crypto
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} - {self.vendeur.username}"

class PanierItem(models.Model):
    utilisateur = models.ForeignKey(
        'Utilisateur',  # Assure-toi que 'Utilisateur' est bien un modèle existant ou remplace par 'User'
        on_delete=models.CASCADE,
        related_name='panier',
        limit_choices_to={'role': 'acheteur'},  # Assure-toi que 'role' existe dans ton modèle 'Utilisateur'
    )
    produit = models.ForeignKey(
        'Produit',  # Assure-toi que le modèle 'Produit' existe et est bien référencé
        on_delete=models.CASCADE
    )
    quantite = models.PositiveIntegerField(default=1)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'produit')  # Empêche l'ajout d'un produit en double pour le même utilisateur

    @property
    def total(self):
        # Calcul du total : produit par quantité
        return self.produit.prix * self.quantite

    def __str__(self):
        return f"{self.quantite}x {self.produit.nom} ({self.utilisateur})"

class Commande(models.Model):
    STATUT_CHOICES = (
        ('en_attente', 'En attente de paiement'),
        ('payee', 'Payée'),
        ('expediee', 'Expédiée'),
        ('annulee', 'Annulée'),
        ('remboursee', 'Remboursée'),
    )
    
    MODE_PAIEMENT = (
        ('crypto', 'Cryptomonnaie'),
        ('espece', 'Espèce'),
    )

    reference = models.CharField(max_length=16, unique=True)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='commandes',
        limit_choices_to={'role': 'acheteur'}
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT,
        default='crypto'
    )
    coinbase_id = models.CharField(max_length=100, blank=True)

    @property
    def total(self):
        return sum(item.sous_total for item in self.items.all())

    def generer_reference(self):
        import secrets
        if not self.reference:
            self.reference = secrets.token_hex(8).upper()

class LigneCommande(models.Model):
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='items'
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.PROTECT
    )
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite

class TransactionCrypto(models.Model):
    CRYPTO_CHOICES = (
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDC', 'USD Coin'),
    )
    
    commande = models.OneToOneField(
        Commande,
        on_delete=models.PROTECT,
        related_name='transaction_crypto'
    )
    crypto = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    montant = models.DecimalField(max_digits=20, decimal_places=8)
    adresse_reception = models.CharField(max_length=100)
    tx_hash = models.CharField(max_length=100)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    confirmations = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.montant} {self.crypto} - {self.commande.reference}"

class JournalAction(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.utilisateur} - {self.action} - {self.date_action}"
    


    
    
    