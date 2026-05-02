# Requirements Document

## Introduction

O FITME é um provador virtual que usa visão computacional para extrair medidas corporais e recomendar tamanhos. Este documento especifica os requisitos para o **Banco Vetorial de Padrões Corporais da População** — uma evolução do sistema de vetores existente que transforma dados individuais de escaneamento em inteligência coletiva. Conforme mais pessoas usam o sistema, o banco acumula dados antropométricos normalizados que permitem recomendações de tamanho mais precisas, análise de padrões corporais da população brasileira, e match inteligente entre corpo e peça de roupa, com acurácia que melhora continuamente (efeito de rede).

## Glossary

- **Vector_Service**: Serviço responsável por normalizar, armazenar e consultar vetores corporais no pgvector
- **Normalization_Engine**: Componente que aplica normalização estatística (z-score) aos vetores de medidas usando parâmetros populacionais
- **Quality_Scorer**: Componente que calcula um score de confiança (0.0–1.0) para cada escaneamento baseado em critérios objetivos
- **Segmentation_Service**: Serviço que classifica e filtra perfis por segmentos demográficos (gênero, faixa etária, região, biotipo)
- **Recommendation_Engine**: Motor de recomendação de tamanho que usa votação ponderada de corpos similares com pesos de qualidade e feedback
- **Population_Analytics**: Serviço de análise estatística que gera insights sobre distribuição corporal da população
- **Anonymization_Service**: Serviço que aplica anonimização e controles de privacidade conforme LGPD
- **Body_Profile**: Registro no banco contendo medidas brutas, vetores normalizados e metadados de um escaneamento corporal
- **Measurements_Vector**: Vetor de 12 dimensões representando medidas corporais normalizadas pela altura
- **Quality_Score**: Valor numérico entre 0.0 e 1.0 que indica a confiabilidade de um escaneamento
- **Population_Stats**: Estatísticas agregadas (média, desvio padrão) calculadas a partir dos perfis do banco, usadas para normalização z-score
- **Similarity_Search**: Busca por vizinhos mais próximos usando distância coseno no pgvector
- **LGPD**: Lei Geral de Proteção de Dados — legislação brasileira de proteção de dados pessoais

## Requirements

### Requirement 1: Vector Normalization Strategy

**User Story:** As a developer, I want body measurement vectors to be statistically normalized using population-level parameters, so that similarity searches produce accurate results regardless of absolute body size.

#### Acceptance Criteria

1. WHEN a Body_Profile is saved, THE Normalization_Engine SHALL compute a z-score normalized vector using the current Population_Stats (mean and standard deviation per dimension)
2. THE Normalization_Engine SHALL store both the raw Measurements_Vector and the z-score normalized vector in each Body_Profile
3. WHEN Population_Stats are recalculated, THE Normalization_Engine SHALL use only Body_Profiles with a Quality_Score above 0.5
4. THE Vector_Service SHALL use the z-score normalized vector for all Similarity_Search operations
5. WHEN the number of Body_Profiles in the database is fewer than 30, THE Normalization_Engine SHALL fall back to height-ratio normalization instead of z-score normalization
6. THE Normalization_Engine SHALL recalculate Population_Stats when triggered by a scheduled job or manual API call
7. FOR ALL valid Measurements_Vectors, normalizing then denormalizing using the same Population_Stats SHALL produce a vector within 0.001 tolerance of the original (round-trip property)

### Requirement 2: Data Quality Scoring

**User Story:** As a system operator, I want each body scan to receive a quality score, so that low-confidence scans have reduced influence on population statistics and recommendations.

#### Acceptance Criteria

1. WHEN a body scan is processed, THE Quality_Scorer SHALL compute a Quality_Score between 0.0 and 1.0
2. THE Quality_Scorer SHALL factor in the number of MediaPipe landmarks detected (out of 33) as a component of the Quality_Score
3. THE Quality_Scorer SHALL factor in the number of distinct angles captured during a 360° scan as a component of the Quality_Score
4. THE Quality_Scorer SHALL factor in the consistency of height estimates across multiple frames as a component of the Quality_Score
5. THE Quality_Scorer SHALL factor in whether a reference height was provided by the user as a component of the Quality_Score
6. WHEN a Body_Profile has a Quality_Score below 0.3, THE Vector_Service SHALL exclude that profile from Similarity_Search results
7. THE Quality_Scorer SHALL store the Quality_Score and its individual component scores in the Body_Profile record

### Requirement 3: Population Segmentation

**User Story:** As a data analyst, I want body profiles to be segmented by demographic attributes, so that similarity searches and analytics can be scoped to relevant population groups.

#### Acceptance Criteria

1. THE Body_Profile SHALL store optional demographic metadata: gender (string), age_range (string enum: "18-25", "26-35", "36-45", "46-55", "56+"), and region (string, Brazilian state code)
2. WHEN a Similarity_Search is performed with segment filters, THE Vector_Service SHALL restrict results to Body_Profiles matching the specified gender, age_range, or region
3. WHEN no segment filters are provided, THE Vector_Service SHALL search across all Body_Profiles
4. THE Segmentation_Service SHALL classify each Body_Profile into a body_type category (triangulo, triangulo_invertido, retangulo, ampulheta, oval) based on shoulder-to-hip and waist-to-hip ratios
5. WHEN segment filters are applied, THE Vector_Service SHALL return only profiles that match all specified filter criteria simultaneously

### Requirement 4: Accuracy Improvement Loop

**User Story:** As a product owner, I want the recommendation accuracy to improve as more users provide feedback, so that the system exhibits a network effect where more data leads to better results.

#### Acceptance Criteria

1. WHEN a user provides post-purchase feedback (rating, purchased, returned), THE Recommendation_Engine SHALL store the feedback linked to the corresponding TryOnHistory record
2. THE Recommendation_Engine SHALL weight similarity votes by a composite score that combines cosine similarity, Quality_Score of the matching profile, and post-purchase feedback
3. WHEN a matching profile has a purchased=1 and returned=0 feedback, THE Recommendation_Engine SHALL apply a 1.5x weight multiplier to that profile's vote
4. WHEN a matching profile has a returned=1 feedback, THE Recommendation_Engine SHALL apply a 0.3x weight multiplier to that profile's vote
5. THE Population_Analytics SHALL track recommendation accuracy over time by comparing recommended sizes against actual purchase and return outcomes
6. WHEN the Recommendation_Engine produces a size recommendation, THE Recommendation_Engine SHALL include a confidence score calculated as the proportion of weighted votes for the winning size relative to total weighted votes

### Requirement 5: Size Recommendation Engine

**User Story:** As a customer, I want to receive a size recommendation based on what people with similar bodies purchased and kept, so that I can choose the right size with confidence.

#### Acceptance Criteria

1. WHEN a size recommendation is requested for a garment, THE Recommendation_Engine SHALL find the top N most similar Body_Profiles that have TryOnHistory for that garment
2. THE Recommendation_Engine SHALL compute a weighted vote for each size, where the weight combines cosine similarity and Quality_Score
3. THE Recommendation_Engine SHALL return the size with the highest weighted vote total as the recommended size
4. THE Recommendation_Engine SHALL return a size distribution showing the percentage of weighted votes for each size
5. WHEN fewer than 5 similar profiles have TryOnHistory for the requested garment, THE Recommendation_Engine SHALL indicate low confidence in the response
6. THE Recommendation_Engine SHALL accept an optional segment filter (gender, age_range) to scope the similar body search
7. IF no Body_Profiles with TryOnHistory for the requested garment are found, THEN THE Recommendation_Engine SHALL return a 404 response with a descriptive message

### Requirement 6: Population Analytics and Insights

**User Story:** As a data analyst, I want to query aggregate statistics about the body profile population, so that I can understand body type distributions, measurement trends, and size curves.

#### Acceptance Criteria

1. THE Population_Analytics SHALL provide an endpoint that returns the distribution of body types (count and percentage per type) across all Body_Profiles
2. THE Population_Analytics SHALL provide an endpoint that returns percentile statistics (p5, p25, p50, p75, p95) for each body measurement dimension
3. WHEN segment filters are provided, THE Population_Analytics SHALL scope the statistics to Body_Profiles matching the specified filters
4. THE Population_Analytics SHALL provide an endpoint that returns the total number of Body_Profiles, the number with Quality_Score above 0.5, and the average Quality_Score
5. THE Population_Analytics SHALL provide an endpoint that returns size recommendation accuracy metrics: total recommendations made, percentage where the recommended size was purchased, and percentage where the purchased item was returned

### Requirement 7: Privacy and LGPD Compliance

**User Story:** As a system operator, I want body data to be stored with proper anonymization and consent controls, so that the system complies with LGPD requirements.

#### Acceptance Criteria

1. THE Anonymization_Service SHALL ensure that Population_Analytics endpoints return only aggregate data with a minimum group size of 10 profiles per segment
2. WHEN a user requests deletion of their data, THE Anonymization_Service SHALL delete all Body_Profiles and TryOnHistory records linked to that external_user_id within 48 hours
3. THE Body_Profile SHALL store a consent_given flag (boolean) indicating whether the user consented to population-level data usage
4. WHEN consent_given is false, THE Vector_Service SHALL exclude that Body_Profile from Similarity_Search results and Population_Analytics aggregations
5. THE Anonymization_Service SHALL provide a data export endpoint that returns all Body_Profiles and TryOnHistory linked to a given external_user_id in JSON format
6. THE Anonymization_Service SHALL not expose raw landmark vectors or individual measurement vectors in any Population_Analytics response

### Requirement 8: Normalization Round-Trip Integrity

**User Story:** As a developer, I want to verify that the normalization and denormalization process preserves measurement data accurately, so that I can trust the normalized vectors for similarity search.

#### Acceptance Criteria

1. FOR ALL valid Measurements_Vectors, THE Normalization_Engine SHALL satisfy the round-trip property: denormalize(normalize(v, stats), stats) produces a vector within 0.001 Euclidean distance of v
2. THE Normalization_Engine SHALL expose a normalize function that accepts a raw vector and Population_Stats and returns a z-score normalized vector
3. THE Normalization_Engine SHALL expose a denormalize function that accepts a normalized vector and Population_Stats and returns the original-scale vector
