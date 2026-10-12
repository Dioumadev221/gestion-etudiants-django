from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Document, Filiere, Profil, role_de
from .permissions import EstAdminOuResponsable, IsAdminOrReadOnly
from .serializers import (
    ConnexionSerializer,
    DocumentSerializer,
    EtudiantListeSerializer,
    FiliereSerializer,
    InscriptionSerializer,
    UtilisateurSerializer,
)


# 1. Page d'accueil
@api_view(['GET'])
@permission_classes([AllowAny])
def accueil(request):
    data = {
        'message': 'Bienvenue sur la plateforme de gestion des étudiants.',
        'filieres': FiliereSerializer(Filiere.objects.all(), many=True).data,
    }
    if request.user.is_authenticated:
        data['utilisateur'] = UtilisateurSerializer(request.user, context={'request': request}).data
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def liste_filieres(request):
    return Response(FiliereSerializer(Filiere.objects.all(), many=True).data)


# 2. Inscription (publique pour un étudiant, ou par l'admin depuis son dashboard)
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def inscription(request):
    serializer = InscriptionSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# 3. Connexion / déconnexion
class ConnexionView(TokenObtainPairView):
    serializer_class = ConnexionSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deconnexion(request):
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({'detail': 'Le refresh token est requis.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh)
        if str(token['user_id']) != str(request.user.id):
            raise TokenError('Token étranger')
        token.blacklist()
    except TokenError:
        return Response({'detail': 'Token invalide ou déjà expiré.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Déconnexion réussie.'}, status=status.HTTP_205_RESET_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def moi(request):
    return Response(UtilisateurSerializer(request.user, context={'request': request}).data)


# 4. Liste des étudiants (prénom, nom, filière) – admin et responsable
@api_view(['GET'])
@permission_classes([EstAdminOuResponsable])
def liste_etudiants(request):
    etudiants = Profil.objects.filter(role=Profil.Role.ETUDIANT).select_related('user', 'filiere')
    filiere = request.query_params.get('filiere')
    if filiere:
        etudiants = etudiants.filter(filiere_id=filiere)
    return Response(EtudiantListeSerializer(etudiants, many=True).data)


class DocumentViewSet(viewsets.ModelViewSet):
    """Seuls les admins ajoutent des documents ; l'étudiant consulte les siens."""

    serializer_class = DocumentSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Document.objects.select_related('etudiant', 'ajoute_par')
        if role_de(self.request.user) == Profil.Role.ADMIN:
            return qs
        return qs.filter(etudiant__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(ajoute_par=self.request.user)
