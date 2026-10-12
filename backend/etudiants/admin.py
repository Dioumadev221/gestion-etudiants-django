from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Document, Filiere, Profil


class ProfilInline(admin.StackedInline):
    """Permet à l'admin de créer un utilisateur et son profil en même temps."""

    model = Profil
    can_delete = False
    min_num = 1
    fields = ['role', 'filiere', 'photo', 'telephone']


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    exclude = ['ajoute_par']


admin.site.unregister(User)


@admin.register(User)
class UtilisateurAdmin(UserAdmin):
    inlines = [ProfilInline]
    list_display = ['username', 'first_name', 'last_name', 'email', 'role', 'filiere']
    list_filter = ['profil__role', 'profil__filiere', 'is_active']

    @admin.display(description='rôle')
    def role(self, user):
        profil = getattr(user, 'profil', None)
        return profil.get_role_display() if profil else '-'

    @admin.display(description='filière')
    def filiere(self, user):
        profil = getattr(user, 'profil', None)
        return profil.filiere if profil and profil.filiere else '-'


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    search_fields = ['nom']


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'filiere']
    list_filter = ['role', 'filiere']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    inlines = [DocumentInline]

    def save_formset(self, request, form, formset, change):
        # Enregistre l'admin connecté comme auteur des documents ajoutés
        for doc in formset.save(commit=False):
            if not doc.ajoute_par_id:
                doc.ajoute_par = request.user
            doc.save()
        for doc in formset.deleted_objects:
            doc.delete()
        formset.save_m2m()


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['titre', 'etudiant', 'ajoute_par', 'date_ajout']
    search_fields = ['titre', 'etudiant__user__last_name']
    exclude = ['ajoute_par']

    def save_model(self, request, obj, form, change):
        if not obj.ajoute_par_id:
            obj.ajoute_par = request.user
        super().save_model(request, obj, form, change)
