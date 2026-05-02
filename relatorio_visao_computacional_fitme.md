# Análise Técnica de Visão Computacional: Provador Virtual FITME

**Autor:** Manus AI  
**Data:** Maio de 2026  
**Repositório Analisado:** `LiviaMor/fitme`

## 1. Resumo Executivo

O projeto FITME apresenta uma implementação de provador virtual baseada em uma arquitetura de visão computacional clássica (2D), utilizando a biblioteca MediaPipe para extração de pontos-chave corporais (landmarks) e OpenCV para manipulação de imagens. A solução atual foca em viabilizar um Produto Mínimo Viável (MVP) rápido e de baixo custo computacional, operando através da sobreposição bidimensional de peças de roupa (overlay) sobre a silhueta do usuário. 

Apesar de ser funcional para demonstrações iniciais e não exigir hardware especializado (GPUs) no backend, a abordagem apresenta limitações intrínsecas significativas em relação ao realismo visual, adaptação tridimensional das peças e preservação de iluminação e texturas. O próprio código-fonte documenta a intenção de evoluir a arquitetura para modelos baseados em difusão (como IDM-VTON ou OOTDiffusion) em fases futuras do produto [1].

## 2. Arquitetura Atual de Visão Computacional

O pipeline de processamento visual do FITME está concentrado principalmente no serviço `VirtualTryOn` (`fitme-api/app/services/virtual_tryon.py`). O fluxo operacional atual segue uma sequência determinística de etapas clássicas de processamento de imagem.

A primeira etapa consiste na recepção e normalização das imagens. O sistema aceita a foto do cliente e a imagem da roupa (via upload ou URL), aplicando a função utilitária `fix_orientation` para corrigir problemas de rotação introduzidos pelos metadados EXIF de câmeras de smartphones. Este passo é crucial, pois as redes neurais de detecção de pose são altamente sensíveis à orientação da imagem.

Em seguida, ocorre a extração de características corporais. A imagem do cliente é processada pelo `MediaPipe Pose`, configurado com `model_complexity=2` para priorizar precisão em detrimento da velocidade extrema. O sistema verifica a visibilidade de seis pontos essenciais: ombros esquerdo e direito (landmarks 11 e 12), quadris (23 e 24) e tornozelos (27 e 28). Caso qualquer um destes pontos apresente uma pontuação de confiança inferior a 0.3, o processamento é abortado, garantindo que apenas imagens de corpo inteiro adequadas sejam processadas.

A terceira fase é o isolamento da peça de roupa. O sistema implementa uma técnica de remoção de fundo baseada em limiarização de cores no espaço HSV (Hue, Saturation, Value). Duas máscaras são criadas para detectar fundos brancos e cinza-claros, que são combinadas, dilatadas e invertidas para extrair a peça de roupa e convertê-la para o formato BGRA (com canal de transparência alfa).

A etapa final é o posicionamento e sobreposição. Baseado no tipo de peça selecionado (camiseta, calça, vestido, etc.), o sistema calcula uma região retangular (bounding box) usando as distâncias entre os landmarks corporais. Um aspecto interessante da implementação é o cálculo do ângulo dos ombros utilizando a função arco-tangente, permitindo que a imagem da roupa seja rotacionada via `cv2.warpAffine` para acompanhar a inclinação do corpo do usuário antes de ser sobreposta à imagem original com uma opacidade ajustável.

## 3. Avaliação Técnica e Limitações

A implementação atual demonstra um bom domínio das ferramentas clássicas de visão computacional, com atenção a detalhes importantes como a rotação adaptativa dos ombros e a correção de orientação EXIF. O uso do MediaPipe garante inferência rápida, permitindo que a API processe requisições em hardware padrão (CPU) com baixa latência.

No entanto, a abordagem de "overlay 2D" possui barreiras arquitetônicas intransponíveis quando o objetivo é alcançar fotorrealismo. O sistema atual não consegue modelar a deformação tridimensional do tecido sobre o volume do corpo, resultando em um aspecto visual de "recorte de papel" (paper doll effect). As dobras naturais da roupa, o caimento (drape), as sombras projetadas pelo corpo e a iluminação ambiente da foto original do usuário são completamente ignorados durante o processo de sobreposição [2].

Além disso, o método de remoção de fundo por espaço de cor HSV (`cv2.inRange`) é frágil e sujeito a falhas. Se a peça de roupa contiver cores claras semelhantes ao fundo (como uma camiseta branca), partes da própria peça serão erroneamente removidas. Técnicas modernas de segmentação semântica, como o Segment Anything Model (SAM) ou U-Net-based matting, ofereceriam resultados significativamente superiores para esta tarefa específica.

A extração de medidas corporais, implementada no serviço `MultiFrameScanner360`, representa a parte mais sofisticada do repositório em termos algorítmicos. O sistema tenta contornar a limitação de profundidade de câmeras monoculares combinando múltiplos frames capturados em ângulos diferentes (0°, 90°, 180°, 270°) e aplicando a fórmula de aproximação de Ramanujan para elipses na tentativa de calcular circunferências reais. Pesquisas recentes indicam que o MediaPipe, por ter sido treinado focado em cinemática e rastreamento de movimento, tende a subestimar as larguras corporais, especialmente em silhuetas femininas [3]. A abordagem do FITME de usar múltiplas vistas mitiga parcialmente este problema, mas ainda depende de calibração baseada na altura informada pelo usuário.

## 4. Análise de Alternativas Tecnológicas (Estado da Arte)

O mercado de Virtual Try-On (VTON) evoluiu drasticamente com a introdução de modelos de difusão (Diffusion Models). O código-fonte do FITME menciona explicitamente a intenção de migrar para tecnologias como IDM-VTON ou OOTDiffusion. Abaixo, apresentamos uma comparação das principais alternativas open-source disponíveis atualmente [4].

| Modelo / Tecnologia | Arquitetura Base | Vantagens Principais | Limitações e Desafios |
|---------------------|------------------|----------------------|-----------------------|
| **Overlay (Atual)** | OpenCV + MediaPipe | Custo zero, latência em milissegundos, roda em CPU. | Fotorrealismo nulo, sem caimento 3D, remoção de fundo frágil. |
| **VITON-HD** | GANs (Generative Adversarial Networks) | Resolução superior a métodos antigos (1024x768), warping razoável. | Artefatos em áreas desalinhadas, perda de detalhes finos da textura da roupa. |
| **OOTDiffusion** | Stable Diffusion 1.5 (Dual UNet) | Boa integração da roupa, suporta prompts de texto auxiliares. | Não suporta peças da parte inferior (calças), código legado apresenta instabilidades. |
| **IDM-VTON** | Stable Diffusion XL (SDXL) | Excelente preservação de textura, adaptação realista de luz e sombra. | Requer GPUs potentes (VRAM > 16GB), latência alta (20 a 70 segundos por imagem). |
| **CatVTON** | Concatenation-based Diffusion | Mais eficiente computacionalmente que o IDM-VTON, alta qualidade. | Ainda exige infraestrutura de GPU dedicada para produção. |

## 5. Recomendações e Plano de Evolução

Para elevar o provador virtual do FITME a um padrão de mercado comercialmente competitivo, a transição para modelos baseados em difusão é o caminho tecnicamente correto. O IDM-VTON (Improved Diffusion Models for Virtual Try-On) desponta atualmente como a solução open-source mais robusta para preservação de detalhes da roupa (como estampas, botões e texturas complexas) [5].

### 5.1. Evolução de Curto Prazo (Melhorias no MVP)

Antes de uma migração completa para redes neurais generativas pesadas, o pipeline atual pode ser aprimorado substituindo a remoção de fundo baseada em HSV por um modelo de segmentação semântica leve. A integração da biblioteca `rembg` (baseada na arquitetura U^2-Net) melhoraria drasticamente o recorte das peças de roupa sem exigir GPUs dedicadas. 

Além disso, a extração de contornos corporais pode ser refinada. Atualmente, o cálculo das "bounding boxes" para posicionamento das roupas é estático e baseado apenas nos extremos dos ombros e quadris. A aplicação de algoritmos de Thin Plate Spline (TPS) warping usando os landmarks do MediaPipe como pontos de controle permitiria uma deformação básica da imagem da roupa, ajustando-a melhor à silhueta do usuário antes do blend final.

### 5.2. Evolução de Médio/Longo Prazo (Arquitetura Generativa)

A implementação de modelos de difusão como o IDM-VTON ou CatVTON exigirá uma mudança arquitetônica profunda no backend do FITME. O processamento não poderá mais ocorrer de forma síncrona no request HTTP do FastAPI devido à alta latência da geração (frequentemente superior a 20 segundos mesmo em GPUs de última geração).

A nova arquitetura deverá adotar um padrão assíncrono com filas de mensagens (como Celery e Redis ou RabbitMQ). O usuário enviaria as imagens e receberia um `job_id`, fazendo *polling* ou recebendo notificações via WebSockets quando o processamento em GPU fosse concluído. 

Considerando os custos de infraestrutura para manter instâncias GPU ativas 24/7 na AWS ou GCP, uma alternativa financeiramente viável para startups é o consumo de APIs comerciais especializadas em Virtual Try-On. Serviços como FASHN.ai oferecem endpoints otimizados para esta finalidade, cobrando frações de centavo de dólar por imagem gerada e abstraindo a complexidade de gerenciar instâncias de inferência pesadas [6].

## 6. Referências

[1] Código-fonte do repositório `LiviaMor/fitme`, arquivo `fitme-api/app/services/virtual_tryon.py`.
[2] Islam, T., et al. "Image-based virtual try-on: Fidelity and simplification." ScienceDirect, 2024.
[3] Zong, W., Yang, J., Baytar, F. "Predicting Human Body Measurements Using MediaPipe Pose Auto-Capture." Proceedings of 3DBODY.TECH, 2023.
[4] Khazaeepoul, P. "Comparing the Top 4 Open Source Virtual Try On (VITON) Models." FASHN.ai Blog, 2025.
[5] "Improving diffusion models for authentic virtual try-on in the wild." Springer, 2024.
[6] FASHN.ai Virtual Try-On API Documentation. Disponível em: https://fashn.ai/products/api
