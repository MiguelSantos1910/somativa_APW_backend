# MangeFlix: Backend

API REST da plataforma **MangeFlix**, feita com Django REST Framework. Ela cuida do cadastro e login de usuários (JWT), do catálogo de filmes e da lista de favoritos de cada usuário.

O frontend (Vue.js) fica em um repositório separado.

## Tecnologias

- Python 3.11+
- Django 5.2 e Django REST Framework
- Simple JWT (autenticação com access e refresh token, logout com blacklist)
- django-filter (busca, filtro por gênero e ordenação)
- django-environ (configuração por variáveis de ambiente)
- SQLite

## Como executar

```bash
# 1. Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Configurar as variáveis de ambiente
cp .env.example .env              # depois troque o SECRET_KEY

# 4. Criar o banco e carregar os filmes
python manage.py migrate
python manage.py loaddata filmes

# 5. Criar um administrador (opcional, para acessar /admin e as telas de admin)
python manage.py createsuperuser

# 6. Subir o servidor
python manage.py runserver
```

A API fica em `http://localhost:8000/api/` e o Django Admin em `http://localhost:8000/admin/`.

Para gerar um `SECRET_KEY` novo:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Variáveis de ambiente (`.env`)

| Variável | Descrição | Exemplo |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Django (obrigatória) | `troque-por-uma-chave` |
| `DEBUG` | Modo de desenvolvimento. Precisa estar `True` para o Django servir os pôsteres | `True` |
| `ALLOWED_HOSTS` | Hosts aceitos, separados por vírgula | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Endereços do frontend autorizados | `http://localhost:5173` |

## Testes

```bash
python manage.py test
```

São 35 testes unitários cobrindo cadastro, login (por usuário ou e-mail), logout, permissões, catálogo e favoritos. Também está coberta a regra de não duplicar favoritos, de cada usuário ver só os seus e de os favoritos continuarem salvos após o logout.

O GitHub Actions roda os testes a cada push nas branches `master` e `dev` (veja `.github/workflows/ci.yml`).

## Estrutura

```
configuracao/   settings, urls principais
contas/         usuários: models (Conta/papel), serializers, views, permissions, tests
filmes/         catálogo: models (Filme), serializers, views, permissions, tests
filmes/fixtures/filmes.json   11 filmes com sinopse e pôster
media/filmes/   pôsteres dos filmes da fixture
```

## Endpoints

Todas as rotas, exceto cadastro e login, exigem o cabeçalho `Authorization: Bearer <access>`.

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/api/usuarios/` | Cadastrar usuário | público |
| POST | `/api/token/` | Login (usuário **ou** e-mail + senha). Retorna `access` e `refresh` | público |
| POST | `/api/token/refresh/` | Renovar o token de acesso | público |
| POST | `/api/logout/` | Logout (invalida o `refresh`) | logado |
| GET | `/api/me/` | Dados do usuário logado | logado |
| GET | `/api/filmes/` | Listar filmes (`?search=`, `?genero=`, `?ordering=-nota`, `?favoritos=true`) | logado |
| GET | `/api/filmes/{id}/` | Consultar filme | logado |
| POST | `/api/filmes/{id}/favoritar/` | Adicionar aos favoritos | logado |
| DELETE | `/api/filmes/{id}/favoritar/` | Remover dos favoritos | logado |
| POST/PATCH/DELETE | `/api/filmes/` e `/api/filmes/{id}/` | Gerenciar o catálogo | admin |
| GET/PATCH/DELETE | `/api/usuarios/` e `/api/usuarios/{id}/` | Gerenciar usuários | admin (o espectador vê só a si mesmo) |

A lista de favoritos é a relação `favoritado_por` (ManyToMany entre `Filme` e `User`). O usuário sempre vem do token, nunca de um ID enviado pelo frontend, e o banco impede o mesmo par usuário-filme duas vezes.

## Branches

- `master`: versão estável (produção)
- `dev`: desenvolvimento
