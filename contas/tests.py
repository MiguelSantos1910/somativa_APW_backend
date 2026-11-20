from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conta

SENHA = "SenhaForte#2026"


def criar_usuario(username, papel=Conta.Papel.ESPECTADOR, **extra):
    usuario = User.objects.create_user(username=username, password=SENHA, email=f"{username}@teste.com", **extra)
    Conta.objects.filter(usuario=usuario).update(papel=papel)
    usuario.refresh_from_db()
    return usuario


class CadastroTests(APITestCase):
    url = "/api/usuarios/"

    def dados(self, **extra):
        return {"username": "maria", "first_name": "Maria", "email": "maria@teste.com", "password": SENHA, **extra}

    def test_cadastro_cria_usuario_espectador(self):
        resp = self.client.post(self.url, self.dados(), format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["papel"], Conta.Papel.ESPECTADOR)
        self.assertNotIn("password", resp.data)
        usuario = User.objects.get(username="maria")
        self.assertTrue(usuario.check_password(SENHA))

    def test_email_e_obrigatorio(self):
        resp = self.client.post(self.url, self.dados(email=""), format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_email_duplicado_e_recusado(self):
        User.objects.create_user("joao", "MARIA@teste.com", SENHA)

        resp = self.client.post(self.url, self.dados(), format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_senha_fraca_e_recusada(self):
        resp = self.client.post(self.url, self.dados(password="123"), format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", resp.data)

    def test_visitante_nao_pode_se_cadastrar_como_admin(self):
        resp = self.client.post(self.url, self.dados(papel=Conta.Papel.ADMIN), format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="maria").exists())


class LoginTests(APITestCase):
    url = "/api/token/"

    def setUp(self):
        self.usuario = criar_usuario("ana")

    def test_login_com_usuario(self):
        resp = self.client.post(self.url, {"username": "ana", "password": SENHA}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_com_email(self):
        resp = self.client.post(self.url, {"username": "ana@teste.com", "password": SENHA}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_ignora_maiusculas_no_usuario(self):
        resp = self.client.post(self.url, {"username": "  ANA ", "password": SENHA}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_senha_errada_retorna_401(self):
        resp = self.client.post(self.url, {"username": "ana", "password": "errada"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_retorna_usuario_logado(self):
        token = self.client.post(self.url, {"username": "ana", "password": SENHA}, format="json").data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get("/api/me/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "ana")
        self.assertEqual(resp.data["papel"], Conta.Papel.ESPECTADOR)

    def test_me_exige_autenticacao(self):
        self.assertEqual(self.client.get("/api/me/").status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    def setUp(self):
        criar_usuario("ana")
        self.tokens = self.client.post("/api/token/", {"username": "ana", "password": SENHA}, format="json").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tokens['access']}")

    def test_logout_invalida_refresh_token(self):
        resp = self.client.post("/api/logout/", {"refresh": self.tokens["refresh"]}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post("/api/token/refresh/", {"refresh": self.tokens["refresh"]}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_sem_refresh_retorna_400(self):
        resp = self.client.post("/api/logout/", {}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class GestaoUsuariosTests(APITestCase):
    def setUp(self):
        self.admin = criar_usuario("admin", Conta.Papel.ADMIN)
        self.espectador = criar_usuario("espectador")

    def test_espectador_ve_apenas_a_si_mesmo(self):
        self.client.force_authenticate(self.espectador)

        resp = self.client.get("/api/usuarios/")

        self.assertEqual([u["username"] for u in resp.data], ["espectador"])

    def test_admin_ve_todos(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.get("/api/usuarios/")

        self.assertEqual(len(resp.data), 2)

    def test_espectador_nao_altera_papel(self):
        self.client.force_authenticate(self.espectador)

        resp = self.client.patch(f"/api/usuarios/{self.espectador.pk}/", {"papel": "ADMIN"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.espectador.conta.refresh_from_db()
        self.assertEqual(self.espectador.conta.papel, Conta.Papel.ESPECTADOR)

    def test_admin_altera_papel(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.patch(f"/api/usuarios/{self.espectador.pk}/", {"papel": "ADMIN"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["papel"], Conta.Papel.ADMIN)

    def test_admin_nao_administra_superusuario(self):
        superusuario = User.objects.create_superuser("root", "root@teste.com", SENHA)
        self.client.force_authenticate(self.admin)

        resp = self.client.patch(f"/api/usuarios/{superusuario.pk}/", {"is_active": False}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_nao_exclui_a_propria_conta(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.delete(f"/api/usuarios/{self.admin.pk}/")

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_superusuario_recebe_papel_admin(self):
        superusuario = User.objects.create_superuser("root", "root@teste.com", SENHA)

        self.assertEqual(superusuario.conta.papel, Conta.Papel.ADMIN)
