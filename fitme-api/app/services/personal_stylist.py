"""
Personal Stylist com IA.

Recebe o perfil corporal completo do cliente (medidas, biotipo, tom de pele)
e gera uma consultoria de estilo personalizada com sugestões de peças,
cores, cortes e combinações que valorizam o corpo.

Diferencial FITME: não é só "essa roupa fica bonita" — é
"essa roupa CABE em você e valoriza seu corpo".
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings


STYLIST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é um personal stylist profissional de alto nível, 
especialista em moda brasileira e consultoria de imagem.

Seu diferencial: você tem as MEDIDAS EXATAS do cliente. Não é achismo — 
são dados reais extraídos por visão computacional.

Responda SEMPRE em português brasileiro, de forma calorosa e profissional.
Use um tom de consultor premium — como se estivesse numa sessão particular
de personal styling numa boutique de luxo.

Forneça sua resposta no seguinte formato JSON:
{{
    "perfil_resumo": "<resumo do perfil corporal em 2 frases>",
    "biotipo_analise": "<análise detalhada do biotipo e o que valorizar>",
    "cores_recomendadas": [
        {{"cor": "<nome>", "hex": "<#hex>", "motivo": "<por que combina>"}}
    ],
    "cores_evitar": [
        {{"cor": "<nome>", "motivo": "<por que evitar>"}}
    ],
    "pecas_recomendadas": [
        {{
            "tipo": "<tipo da peça>",
            "descricao": "<descrição específica>",
            "tamanho_sugerido": "<PP/P/M/G/GG/XG>",
            "medida_referencia": "<ex: busque ombro 42cm>",
            "motivo": "<por que essa peça valoriza>"
        }}
    ],
    "look_completo": {{
        "ocasiao": "<casual/trabalho/festa/etc>",
        "pecas": ["<peça 1>", "<peça 2>", "<peça 3>"],
        "descricao": "<como montar o look>",
        "dica_extra": "<dica de styling>"
    }},
    "dicas_gerais": [
        "<dica 1>",
        "<dica 2>",
        "<dica 3>"
    ]
}}"""),
    ("human", """Faça uma consultoria de estilo completa para este cliente:

**MEDIDAS CORPORAIS (dados reais, extraídos por scanner):**
- Altura: {height_cm}cm
- Ombros: {shoulder_cm}cm
- Busto/Tórax: {bust_cm}cm (circunferência)
- Cintura: {waist_cm}cm (circunferência)
- Quadril: {hip_cm}cm (circunferência)
- Comprimento ideal de calça: {pants_cm}cm
- Comprimento ideal de camisa: {shirt_cm}cm
- Altura da cava: {armhole_cm}cm

**PERFIL:**
- Biotipo: {body_type}
- Tom de pele: {skin_color} (subtom {skin_undertone})
- Gênero: {gender}
- Ocasião desejada: {occasion}

Com base nas medidas EXATAS, recomende:
1. Cores que combinam com o subtom da pele
2. Peças específicas com tamanho e medidas de referência
3. Um look completo montado
4. Dicas de styling personalizadas

Lembre-se: você tem os dados reais. Seja preciso nos tamanhos."""),
])


class PersonalStylist:
    """Personal Stylist com IA — consultoria baseada em medidas reais."""

    def __init__(self):
        self._llm = None
        self._chain = None

    @property
    def chain(self):
        if self._chain is None:
            self._llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.8,
                api_key=settings.openai_api_key,
            )
            self._chain = STYLIST_PROMPT | self._llm
        return self._chain

    async def consult(
        self,
        height_cm: float,
        shoulder_cm: float = 0,
        bust_cm: float = 0,
        waist_cm: float = 0,
        hip_cm: float = 0,
        pants_cm: float = 0,
        shirt_cm: float = 0,
        armhole_cm: float = 0,
        body_type: str = "não identificado",
        skin_color: str = "não identificado",
        skin_undertone: str = "não identificado",
        gender: str = "não informado",
        occasion: str = "casual",
    ) -> dict:
        """
        Gera consultoria de estilo personalizada.

        Returns:
            Dict com perfil, cores, peças recomendadas, look completo e dicas.
        """
        import json

        response = await self.chain.ainvoke({
            "height_cm": height_cm,
            "shoulder_cm": shoulder_cm or "N/A",
            "bust_cm": bust_cm or "N/A",
            "waist_cm": waist_cm or "N/A",
            "hip_cm": hip_cm or "N/A",
            "pants_cm": pants_cm or round((height_cm * 61) / 100, 1),
            "shirt_cm": shirt_cm or round((height_cm * 45) / 100, 1),
            "armhole_cm": armhole_cm or "N/A",
            "body_type": body_type,
            "skin_color": skin_color,
            "skin_undertone": skin_undertone,
            "gender": gender,
            "occasion": occasion,
        })

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            return {
                "perfil_resumo": "Consultoria gerada com sucesso.",
                "biotipo_analise": response.content[:500],
                "cores_recomendadas": [],
                "cores_evitar": [],
                "pecas_recomendadas": [],
                "look_completo": {
                    "ocasiao": occasion,
                    "pecas": [],
                    "descricao": response.content[:300],
                    "dica_extra": "",
                },
                "dicas_gerais": [response.content[:200]],
            }
