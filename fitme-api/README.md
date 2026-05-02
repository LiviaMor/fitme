# 👗 FITME - Provador Virtual com IA

API e interface para provador virtual inteligente que usa visão computacional e IA generativa para análise corporal, tom de pele e consultoria de estilo.

## 🏗️ Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   FastAPI (API)   │────▶│  OpenAI GPT-4o  │
│   (Front-end)   │     │                  │     │  (Consultoria)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐     ┌──────▼──────┐
              │ MediaPipe  │     │   OpenCV    │
              │ (Medidas)  │     │ (Tom Pele)  │
              └────────────┘     └─────────────┘
```

## 🚀 Quick Start

### 1. Clonar e configurar

```bash
git clone <repo>
cd fitme-api
cp .env.example .env
# Editar .env com sua OPENAI_API_KEY
```

### 2. Instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Rodar a API

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Rodar o Streamlit (outra aba)

```bash
cd streamlit_app
streamlit run app.py
```

### 5. Docker (alternativa)

```bash
docker-compose up --build
```

## 📡 Endpoints da API

### Health Check
```
GET /health
```

### Análise Corporal
```
POST /api/v1/analyze/body
Content-Type: multipart/form-data

- photo: arquivo de imagem (JPEG/PNG/WebP)
- height_cm: altura real em cm (opcional)
```

**Resposta:**
```json
{
  "measurements": {
    "shoulder_width_cm": 42.5,
    "bust_cm": 97.8,
    "waist_cm": 78.4,
    "hip_cm": 96.2,
    "inseam_cm": 78.0,
    "pants_length_cm": 81.9,
    "height_cm": 175.0
  },
  "skin_analysis": {
    "hex_color": "#c4956a",
    "undertone": "quente",
    "color_name": "Pele média"
  },
  "body_type": "retangulo",
  "confidence_score": 0.85,
  "landmarks_detected": 28
}
```

### Análise de Caimento (com LLM)
```
POST /api/v1/analyze/fit
Content-Type: multipart/form-data

- photo: arquivo de imagem
- garment_json: JSON da peça de roupa
- height_cm: altura real em cm (opcional)
```

### Catálogo de Peças
```
GET /api/v1/garments
GET /api/v1/garments?category=vestido&size=M
GET /api/v1/garments/{garment_id}
```

## 🧠 Como Funciona

1. **Input**: Usuário tira foto de corpo inteiro + escolhe peça
2. **MediaPipe**: Detecta 33 landmarks corporais e calcula medidas
3. **OpenCV**: Extrai região da pele e classifica subtom (frio/quente/neutro)
4. **LLM (GPT-4o)**: Recebe medidas + peça e gera consultoria de estilo
5. **Output**: Notas de caimento, cor e recomendação de tamanho

## 🎯 Medidas Extraídas

| Medida | Método |
|--------|--------|
| Ombros | Distância entre landmarks 11-12 |
| Busto | Estimativa proporcional |
| Cintura | Estimativa proporcional |
| Quadril | Distância entre landmarks 23-24 |
| Gancho | Distância quadril-tornozelo |
| Calça | Comprimento interno da perna |

## 📦 Stack Tecnológica

- **Linguagem**: Python 3.11
- **API**: FastAPI + Pydantic
- **Visão Computacional**: MediaPipe + OpenCV
- **IA Generativa**: LangChain + OpenAI GPT-4o
- **Front-end**: Streamlit
- **Deploy**: Docker / AWS App Runner

## 🔧 Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| OPENAI_API_KEY | Chave da API OpenAI | Sim |
| AWS_ACCESS_KEY_ID | AWS Access Key | Não |
| AWS_SECRET_ACCESS_KEY | AWS Secret Key | Não |
| S3_BUCKET_NAME | Bucket para fotos | Não |

## 📄 Licença

MIT - FITME Startup Weekend MVP
