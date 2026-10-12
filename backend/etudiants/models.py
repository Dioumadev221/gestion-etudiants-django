from django.conf import settings
from django.db import models


class Filiere(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'filière'

    def __str__(self):
        return self.nom


class Profil(models.Model):
    """Profil attaché à chaque utilisateur, quel que soit son rôle."""

    class Role(models.TextChoices):
        ETUDIANT = 'etudiant', 'Étudiant'
        ADMIN = 'admin', 'Administrateur'
        RESPONSABLE = 'responsable', 'Responsable formation'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ETUDIANT)
    filiere = models.ForeignKey(
        Filiere, on_delete=models.PROTECT, null=True, blank=True, related_name='profils'
    )
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'


class Document(models.Model):
    """Document ajouté par un administrateur au dossier d'un étudiant."""

    etudiant = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='documents')
    titre = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='documents/')
    ajoute_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_ajoutes',
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_ajout']

    def __str__(self):
        return self.titre


def role_de(user):
    """Rôle effectif d'un utilisateur (un superuser sans profil est admin)."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return Profil.Role.ADMIN
    profil = getattr(user, 'profil', None)
    return profil.role if profil else None
