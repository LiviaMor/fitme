"""
Serviço de consultoria de estilo usando LLM (OpenAI GPT-4o via LangChain).
Recebe medidas corporais, tom de pele e peça de roupa, e retorna consultoria.
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.models.measurements import BodyMeasurements, SkinAnalysis, BodyType
from app.models.garments import Garment, FitResult, GarmentSize


STYLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Você é um consultor de moda profissional e personal stylist.
Sua função é analisar o caimento de peças de roupa com base nas medidas corporais
do cliente e recomendar se a peça é adequada.

Responda SEMPRE em português brasileiro, de forma clara e amigável.
Use um tom profissional mas acessível, como um consultor de moda em uma loja premium.

Forneça sua resposta no seguinte formato JSON:
{{
    "fit_score": <nota de 0 a 10 para o caimento>,
    "color_match_score": <nota de 0 a 10 para combinação de cor>,
    "overall_score": <nota geral de 0 a 10>,
    "fit_description": "<descrição detalhada do caimento>",
    "style_advice": "<consultoria de estilo personalizada>",
    "recommended_size": "<tamanho recomendado: PP, P, M, G, GG ou XG>"
}}"""),
    ("human", """Analise o seguinte cenário:

**CLIENTE:**
- Biotipo: {body_type}
- Largura dos ombros: {shoulder_cm}cm
- Busto: {bust_cm}cm
- Cintura: {waist_cm}cm
- Quadril: {hip_cm}cm
- Comprimento da calça: {pants_length_cm}cm
- Tom de pele: {skin_color} ({skin_undertone})

**PEÇA ESCOLHIDA:**
- Nome: {garment_name}
- Categoria: {garment_category}
- Tamanho: {garment_size}
- Cor: {garment_color}
- Medida do ombro da peça: {garment_shoulder_cm}cm
- Medida do busto da peça: {garment_bust_cm}cm
- Medida da cintura da peça: {garment_waist_cm}cm

O caimento será bom? A cor combina com o subtom {skin_undertone} da pele?
Responda como um consultor de moda profissional."""),
])


class StyleConsultant:
    """Consultor de estilo usando LLM."""

    def __init__(self):
        self._llm = None
        self._chain = None

    @property
    def chain(self):
        """Lazy initialization - só cria a conexão quando necessário."""
        if self._chain is None:
            self._llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                api_key=settings.openai_api_key,
            )
            self._chain = STYLE_PROMPT | self._llm
        return self._chain

    async def analyze_fit(
        self,
        measurements: BodyMeasurements,
        skin_analysis: SkinAnalysis,
        body_type: BodyType,
        garment: Garment,
    ) -> FitResult:
        """
        Analisa o caimento de uma peça para o cliente.

        Args:
            measurements: Medidas corporais do cliente.
            skin_analysis: Análise do tom de pele.
            body_type: Biotipo corporal.
            garment: Peça de roupa a ser analisada.

        Returns:
            FitResult com notas e consultoria.
        """
        import json

        response = await self.chain.ainvoke({
            "body_type": body_type.value,
            "shoulder_cm": measurements.shoulder_width_cm,
            "bust_cm": measurements.bust_cm or "N/A",
            "waist_cm": measurements.waist_cm or "N/A",
            "hip_cm": measurements.hip_cm or "N/A",
            "pants_length_cm": measurements.pants_length_cm or "N/A",
            "skin_color": skin_analysis.color_name,
            "skin_undertone": skin_analysis.undertone.value,
            "garment_name": garment.name,
            "garment_category": garment.category.value,
            "garment_size": garment.size.value,
            "garment_color": garment.color,
            "garment_shoulder_cm": garment.measurements.shoulder_cm or "N/A",
            "garment_bust_cm": garment.measurements.bust_cm or "N/A",
            "garment_waist_cm": garment.measurements.waist_cm or "N/A",
        })

        # Parse da resposta JSON da LLM
        try:
            content = response.content
            # Extrair JSON do texto (pode vir com markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result_data = json.loads(content.strip())

            return FitResult(
                garment_id=garment.id,
                fit_score=float(result_data.get("fit_score", 5)),
                color_match_score=float(result_data.get("color_match_score", 5)),
                overall_score=float(result_data.get("overall_score", 5)),
                fit_description=result_data.get("fit_description", "Análise indisponível"),
                style_advice=result_data.get("style_advice", "Consultoria indisponível"),
                recommended_size=GarmentSize(
                    result_data.get("recommended_size", garment.size.value)
                ),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback se a LLM não retornar JSON válido
            return FitResult(
                garment_id=garment.id,
                fit_score=5.0,
                color_match_score=5.0,
                overall_score=5.0,
                fit_description=response.content[:500],
                style_advice="Não foi possível gerar consultoria estruturada. "
                + response.content[:300],
                recommended_size=garment.size,
            )
