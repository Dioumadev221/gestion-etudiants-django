import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Filiere, Profil

MEDIA_TEST = tempfile.mkdtemp()


def image_test():
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'blue').save(buffer, 'PNG')
    return SimpleUploadedFile('photo.png', buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class ApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.gl = Filiere.objects.get(nom='Génie Logiciel')
        self.ds = Filiere.objects.get(nom='Data Science')
        self.admin = User.objects.create_superuser('admin', password='Admin-test-123')
        resp = User.objects.create_user('resp', password='Resp-test-123')
        Profil.objects.create(user=resp, role=Profil.Role.RESPONSABLE)
        self.creer_etudiant('awa', 'Awa', 'Diop', self.gl)
        self.creer_etudiant('moussa', 'Moussa', 'Ba', self.ds)

    def creer_etudiant(self, username, prenom, nom, filiere):
        user = User.objects.create_user(
            username, password='Etudiant-test-123', first_name=prenom, last_name=nom
        )
        Profil.objects.create(user=user, filiere=filiere)

    def connecter(self, username, password):
        rep = self.client.post('/api/connexion/', {'username': username, 'password': password})
        self.assertEqual(rep.status_code, 200, rep.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {rep.data['access']}")
        return rep.data

    def donnees_inscription(self, **extra):
        data = {
            'username': 'fatou', 'first_name': 'Fatou', 'last_name': 'Sow',
            'email': 'fatou@example.com', 'password': 'Fatou-test-123',
            'filiere': self.gl.id, 'photo': image_test(),
        }
        data.update(extra)
        return data

    # 1. Accueil
    def test_accueil_public(self):
        rep = self.client.get('/api/')
        self.assertEqual(rep.status_code, 200)
        self.assertEqual(len(rep.data['filieres']), 3)

    # 2. Inscription
    def test_inscription_cree_utilisateur_et_profil(self):
        rep = self.client.post('/api/inscription/', self.donnees_inscription(), format='multipart')
        self.assertEqual(rep.status_code, 201, rep.data)
        self.assertNotIn('password', rep.data)
        profil = User.objects.get(username='fatou').profil
        self.assertEqual(profil.role, Profil.Role.ETUDIANT)
        self.assertEqual(profil.filiere, self.gl)
        self.assertTrue(profil.photo)

    def test_inscription_exige_filiere_et_photo(self):
        data = self.donnees_inscription()
        del data['filiere'], data['photo']
        rep = self.client.post('/api/inscription/', data, format='multipart')
        self.assertEqual(rep.status_code, 400)
        self.assertIn('filiere', rep.data)
        self.assertIn('photo', rep.data)

    def test_visiteur_ne_peut_pas_se_donner_un_role(self):
        data = self.donnees_inscription(role='admin')
        rep = self.client.post('/api/inscription/', data, format='multipart')
        self.assertEqual(rep.status_code, 400)
        self.assertIn('role', rep.data)

    def test_admin_cree_un_responsable(self):
        self.connecter('admin', 'Admin-test-123')
        data = self.donnees_inscription(role='responsable')
        rep = self.client.post('/api/inscription/', data, format='multipart')
        self.assertEqual(rep.status_code, 201, rep.data)
        self.assertEqual(rep.data['role'], 'responsable')

    # 3. Connexion / déconnexion
    def test_connexion_renvoie_le_role(self):
        data = self.connecter('resp', 'Resp-test-123')
        self.assertEqual(data['user']['role'], 'responsable')
        self.assertIn('refresh', data)

    def test_connexion_mauvais_mot_de_passe(self):
        rep = self.client.post('/api/connexion/', {'username': 'awa', 'password': 'faux'})
        self.assertEqual(rep.status_code, 401)

    def test_deconnexion_invalide_le_refresh_token(self):
        tokens = self.connecter('awa', 'Etudiant-test-123')
        rep = self.client.post('/api/deconnexion/', {'refresh': tokens['refresh']})
        self.assertEqual(rep.status_code, 205)
        rep = self.client.post('/api/token/refresh/', {'refresh': tokens['refresh']})
        self.assertEqual(rep.status_code, 401)

    # 4. Liste des étudiants
    def test_liste_etudiants_admin(self):
        self.connecter('admin', 'Admin-test-123')
        rep = self.client.get('/api/etudiants/')
        self.assertEqual(rep.status_code, 200)
        self.assertEqual(
            [(e['prenom'], e['nom'], e['filiere']) for e in rep.data],
            [('Moussa', 'Ba', 'Data Science'), ('Awa', 'Diop', 'Génie Logiciel')],
        )

    def test_liste_etudiants_responsable_filtre_par_filiere(self):
        self.connecter('resp', 'Resp-test-123')
        rep = self.client.get('/api/etudiants/', {'filiere': self.gl.id})
        self.assertEqual([e['nom'] for e in rep.data], ['Diop'])

    def test_liste_etudiants_interdite_aux_etudiants(self):
        self.connecter('awa', 'Etudiant-test-123')
        self.assertEqual(self.client.get('/api/etudiants/').status_code, 403)

    def test_liste_etudiants_interdite_sans_connexion(self):
        self.assertEqual(self.client.get('/api/etudiants/').status_code, 401)
