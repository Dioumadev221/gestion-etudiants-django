from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = SimpleRouter()
router.register('documents', views.DocumentViewSet, basename='document')

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('filieres/', views.liste_filieres, name='filieres'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.ConnexionView.as_view(), name='connexion'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('moi/', views.moi, name='moi'),
    path('etudiants/', views.liste_etudiants, name='etudiants'),
    path('', include(router.urls)),
]
