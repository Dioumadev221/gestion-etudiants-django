from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Document, Filiere, Profil, role_de


class FiliereSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filiere
        fields = ['id', 'nom']


class InscriptionSerializer(serializers.Serializer):
    """Crée un utilisateur et son profil en une seule requête (multipart)."""

    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    filiere = serializers.PrimaryKeyRelatedField(queryset=Filiere.objects.all())
    photo = serializers.ImageField()
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    # Seul un admin peut choisir un autre rôle qu'étudiant
    role = serializers.ChoiceField(choices=Profil.Role.choices, required=False)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cet email est déjà utilisé.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role(self, value):
        request = self.context['request']
        if value != Profil.Role.ETUDIANT and role_de(request.user) != Profil.Role.ADMIN:
            raise serializers.ValidationError('Seul un admin peut attribuer ce rôle.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        profil_data = {
            'filiere': validated_data.pop('filiere'),
            'photo': validated_data.pop('photo'),
            'telephone': validated_data.pop('telephone', ''),
            'role': validated_data.pop('role', Profil.Role.ETUDIANT),
        }
        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = profil_data['role'] == Profil.Role.ADMIN
        user.save()
        Profil.objects.create(user=user, **profil_data)
        return user

    def to_representation(self, user):
        return UtilisateurSerializer(user, context=self.context).data


class UtilisateurSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    filiere = serializers.CharField(source='profil.filiere.nom', default=None)
    photo = serializers.ImageField(source='profil.photo', default=None)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'filiere', 'photo']

    def get_role(self, user):
        return role_de(user)


class ConnexionSerializer(TokenObtainPairSerializer):
    """Login JWT : renvoie aussi l'utilisateur et son rôle pour choisir l'espace."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = role_de(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UtilisateurSerializer(self.user, context=self.context).data
        return data


class EtudiantListeSerializer(serializers.ModelSerializer):
    prenom = serializers.CharField(source='user.first_name')
    nom = serializers.CharField(source='user.last_name')
    filiere = serializers.CharField(source='filiere.nom', default=None)

    class Meta:
        model = Profil
        fields = ['id', 'prenom', 'nom', 'filiere']


class DocumentSerializer(serializers.ModelSerializer):
    ajoute_par = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'etudiant', 'titre', 'description', 'fichier', 'ajoute_par', 'date_ajout']
