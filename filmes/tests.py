from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from contas.models import Conta

from .models import Filme

SENHA = "SenhaForte#2026"


def criar_filme(nome="Filme Teste", genero="Drama", **extra):
    dados = {"sinopse": "Uma sinopse.", "nota": "8.0", "duracao": 120, "ano_lancamento": 2020, **extra}
    return Filme.objects.create(nome=nome, genero=genero, **dados)


class CatalogoTests(APITestCase):
    url = "/api/filmes/"

    def setUp(self):
        self.usuario = User.objects.create_user("ana", "ana@teste.com", SENHA)
        self.filme = criar_filme("Parasita", "Suspense")
        criar_filme("Interestelar", "Ficção científica", nota="8.7")

    def test_catalogo_exige_autenticacao(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lista_filmes_com_campos_obrigatorios(self):
        self.client.force_authenticate(self.usuario)

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        for campo in ("nome", "sinopse", "genero", "ano_lancamento", "imagem", "is_favorite"):
            self.assertIn(campo, resp.data[0])

    def test_consulta_filme_por_id(self):
        self.client.force_authenticate(self.usuario)

        resp = self.client.get(f"{self.url}{self.filme.pk}/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["nome"], "Parasita")

    def test_filtra_por_genero(self):
        self.client.force_authenticate(self.usuario)

        resp = self.client.get(self.url, {"genero": "Suspense"})

        self.assertEqual([f["nome"] for f in resp.data], ["Parasita"])

    def test_busca_por_nome(self):
        self.client.force_authenticate(self.usuario)

        resp = self.client.get(self.url, {"search": "inter"})

        self.assertEqual([f["nome"] for f in resp.data], ["Interestelar"])


class GestaoCatalogoTests(APITestCase):
    url = "/api/filmes/"
    dados = {
        "nome": "Novo",
        "genero": "Drama",
        "sinopse": "Sinopse do filme.",
        "nota": "7.5",
        "duracao": 100,
        "ano_lancamento": 2024,
    }

    def setUp(self):
        self.espectador = User.objects.create_user("ana", "ana@teste.com", SENHA)
        self.admin = User.objects.create_user("admin", "admin@teste.com", SENHA)
        Conta.objects.filter(usuario=self.admin).update(papel=Conta.Papel.ADMIN)
        self.admin.refresh_from_db()

    def test_espectador_nao_cadastra_filme(self):
        self.client.force_authenticate(self.espectador)

        resp = self.client.post(self.url, self.dados, format="json")

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Filme.objects.exists())

    def test_admin_cadastra_filme(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.post(self.url, self.dados, format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Filme.objects.get().criado_por, self.admin)

    def test_sinopse_e_obrigatoria(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.post(self.url, {**self.dados, "sinopse": ""}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sinopse", resp.data)

    def test_nota_acima_de_10_e_recusada(self):
        self.client.force_authenticate(self.admin)

        resp = self.client.post(self.url, {**self.dados, "nota": "11"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class FavoritosTests(APITestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana", "ana@teste.com", SENHA)
        self.bia = User.objects.create_user("bia", "bia@teste.com", SENHA)
        self.filme = criar_filme("Parasita")
        self.outro = criar_filme("Interestelar")

    def url_favoritar(self, filme):
        return f"/api/filmes/{filme.pk}/favoritar/"

    def favoritos_de(self, usuario):
        self.client.force_authenticate(usuario)
        return [f["nome"] for f in self.client.get("/api/filmes/", {"favoritos": "true"}).data]

    def test_favoritar_exige_autenticacao(self):
        resp = self.client.post(self.url_favoritar(self.filme))

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_favoritar_e_desfavoritar(self):
        self.client.force_authenticate(self.ana)

        resp = self.client.post(self.url_favoritar(self.filme))
        self.assertEqual(resp.data, {"is_favorite": True})
        self.assertEqual(self.favoritos_de(self.ana), ["Parasita"])

        resp = self.client.delete(self.url_favoritar(self.filme))
        self.assertEqual(resp.data, {"is_favorite": False})
        self.assertEqual(self.favoritos_de(self.ana), [])

    def test_nao_duplica_favorito(self):
        self.client.force_authenticate(self.ana)

        self.client.post(self.url_favoritar(self.filme))
        self.client.post(self.url_favoritar(self.filme))

        self.assertEqual(self.ana.filmes_favoritos.count(), 1)

    def test_cada_usuario_ve_apenas_seus_favoritos(self):
        self.client.force_authenticate(self.ana)
        self.client.post(self.url_favoritar(self.filme))
        self.client.force_authenticate(self.bia)
        self.client.post(self.url_favoritar(self.outro))

        self.assertEqual(self.favoritos_de(self.ana), ["Parasita"])
        self.assertEqual(self.favoritos_de(self.bia), ["Interestelar"])

    def test_is_favorite_e_calculado_por_usuario(self):
        self.client.force_authenticate(self.ana)
        self.client.post(self.url_favoritar(self.filme))

        self.client.force_authenticate(self.bia)
        resp = self.client.get(f"/api/filmes/{self.filme.pk}/")

        self.assertFalse(resp.data["is_favorite"])

    def test_favoritos_continuam_salvos_apos_logout(self):
        tokens = self.client.post("/api/token/", {"username": "ana", "password": SENHA}, format="json").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.client.post(self.url_favoritar(self.filme))
        self.client.post("/api/logout/", {"refresh": tokens["refresh"]}, format="json")
        self.client.credentials()

        tokens = self.client.post("/api/token/", {"username": "ana", "password": SENHA}, format="json").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        resp = self.client.get("/api/filmes/", {"favoritos": "true"})

        self.assertEqual([f["nome"] for f in resp.data], ["Parasita"])
