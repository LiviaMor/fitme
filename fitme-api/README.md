# 👗 FITME - Provador Virtual com IA

API para provador virtual inteligente que usa visão computacional e IA generativa para escaneamento corporal 360°, análise de tom de pele, virtual try-on e consultoria de estilo.

## 🏗️ Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Next.js (Web)  │────▶│   FastAPI (API)   │────▶│  OpenAI GPT-4o  │
│  Vercel Deploy  │     │                  │     │  (Consultoria)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌──────▼──────┐
        │ MediaPipe  │  │  OpenCV   │  │ Try-On      │
        │ Pose 33pts │  │ Skin Tone │  │ Overlay     │
        └────────────┘  └───────────┘  └─────────────┘
```

## 🚀 Quick Start

```bash
git clone https://github.com/LiviaMor/fitme.git
cd fitme/fitme-api
cp .env.example .env
# Editar .env com sua OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Front-end:
```bash
cd fitme/fitme-web
npm install
npm run dev
```

## 📡 Endpoints da API

### Scanner 360° (2 fotos: frente + lado)
```
POST /api/v1/scan360
- front_photo: foto frontal
- side_photo: foto de perfil (lado)
- height_cm: altura real (obrigatória)
```

Retorna circunferências REAIS (busto, cintura, quadril) calculadas
pela fórmula da elipse de Ramanujan usando largura (frente) + profundidade (lado).

### Análise Corporal (1 foto)
```
POST /api/v1/analyze/body
- photo: foto frontal
- height_cm: altura (opcional)
```

### Virtual Try-On
```
POST /api/v1/tryon/url
- photo: foto do cliente
- garment_url: URL da imagem da roupa no e-commerce
- garment_type: camiseta|camisa|vestido|calca|saia|blazer|jaqueta
```

### Consultoria de Estilo (com LLM)
```
POST /api/v1/analyze/fit
- photo: foto do cliente
- garment_json: JSON com dados da peça
```

### Estadiômetro Digital (padrão Welmy)
```
POST /api/v1/stadiometer/measure
- photo: foto corpo inteiro
- model: W200/5 | W200/5A | W110H | Pediátrico
```

### Catálogo
```
GET /api/v1/garments
GET /api/v1/garments/{id}
```

## 📐 Scanner 360° - Como Funciona

```
┌──────────────┐    ┌──────────────┐
│  FOTO FRENTE │    │  FOTO LADO   │
│              │    │              │
│   ←──W──→   │    │   ←──D──→   │
│  (largura)   │    │ (profundid.) │
└──────────────┘    └──────────────┘
        │                   │
        └─────────┬─────────┘
                  │
         Fórmula da Elipse
         C ≈ π[3(a+b) - √((3a+b)(a+3b))]
                  │
                  ▼
        ┌──────────────────┐
        │ CIRCUNFERÊNCIAS  │
        │ Busto: 92cm      │
        │ Cintura: 76cm    │
        │ Quadril: 98cm    │
        └──────────────────┘
```

**Instruções para o usuário:**
1. Foto frontal: de frente, braços levemente afastados do corpo
2. Foto lateral: virado de lado (perfil), braços à frente
3. Ambas: corpo inteiro, fundo claro, roupa justa
4. Informar altura real para calibração

## 🎯 Fórmulas de Modelagem

| Medida | Fórmula |
|--------|---------|
| Altura do gancho | altura × 16 / 100 |
| Comprimento calça | altura × 61 / 100 |
| Comprimento camisa | altura × 45 / 100 |
| Altura da cava | tórax / 4.4 |
| Circunferência | Elipse de Ramanujan (largura + profundidade) |

## 📦 Stack

- **API**: Python 3.11 + FastAPI + Pydantic
- **Visão Computacional**: MediaPipe Pose (33 landmarks) + OpenCV
- **IA Generativa**: LangChain + OpenAI GPT-4o
- **Front-end**: Next.js 16 + Tailwind CSS + TypeScript
- **Deploy**: Vercel (web) + Docker/AWS (API)

## 🔧 Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| OPENAI_API_KEY | Chave da API OpenAI | Só para consultoria |
| AWS_ACCESS_KEY_ID | AWS Access Key | Não |
| AWS_SECRET_ACCESS_KEY | AWS Secret Key | Não |

## 📄 Licença

MIT - FITME Startup Weekend MVP
