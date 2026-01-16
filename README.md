# 🔍 AI Image Detector - KGB-LABS

Este projeto implementa uma ferramenta de **Análise Forense Digital** para imagens, com o objetivo de auxiliar na detecção de manipulações ou de imagens geradas por Inteligência Artificial (IA). A aplicação utiliza uma interface web interativa construída com **Gradio**.

## 🌟 Funcionalidades

O detector realiza uma análise multifacetada da imagem, combinando diversas técnicas de forense digital para gerar um veredito de probabilidade de a imagem ter sido gerada por IA.

| Análise | Descrição |
| :--- | :--- |
| **Análise de Nível de Erro (ELA)** | Detecta inconsistências na compressão JPEG, que podem indicar áreas que foram editadas ou coladas. |
| **Análise de Ruído** | Examina a consistência do ruído da imagem, pois o ruído em imagens geradas por IA ou manipuladas tende a ser menos uniforme. |
| **Análise de Frequência** | Analisa o espectro de frequência da imagem (via Transformada de Fourier) para identificar padrões anormais que não são típicos de fotografias naturais. |
| **Análise de Compressão** | Verifica artefatos de compressão JPEG, comparando a imagem original com uma versão re-comprimida. |
| **Análise de Metadados** | Extrai e verifica a presença de metadados EXIF, cuja ausência ou inconsistência pode ser um indicador de manipulação ou geração artificial. |

## ⚙️ Instalação e Uso

Para configurar e executar o projeto, siga as instruções específicas para o seu sistema operacional.

### 1. Pré-requisitos Comuns

*   Certifique-se de ter o **Python 3** instalado em seu sistema.
*   Salve o código do detector em um arquivo chamado, por exemplo, `ai_detector.py`.
*   Crie o arquivo `requirements.txt` com as dependências listadas abaixo.

```text
gradio
numpy
opencv-python
Pillow
scipy
scikit-image
```

### 2. 🐧 Kali Linux / Outras Distribuições Linux

Recomenda-se o uso de um ambiente virtual para isolar as dependências.

1.  **Navegue** até a pasta do projeto no terminal.
2.  **Crie e ative** o ambiente virtual:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute o programa**:
    ```bash
    python3 ai_detector.py
    ```

### 3. 🪟 Windows

1.  Certifique-se de que o Python está instalado e configurado no `PATH` do sistema.
2.  **Navegue** até a pasta do projeto no Prompt de Comando ou PowerShell.
3.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute o programa**:
    ```bash
    python ai_detector.py
    ```

O servidor será iniciado e você poderá acessar a interface no seu navegador, geralmente em `http://127.0.0.1:8080` (ou o endereço indicado no console).

### Interface de Uso

1.  **Envie a Imagem**: Use o campo "Envie a Imagem" para fazer o upload ou colar a imagem que deseja analisar.
2.  **Analisar Imagem**: Clique no botão "🔍 Analisar Imagem".
3.  **Resultado da Análise**: O relatório detalhado aparecerá na caixa de texto, incluindo o veredito geral e os resultados de cada análise forense.
4.  **Imagem Analisada**: A imagem original será exibida para referência.

## ⚠️ Aviso Importante (Disclaimer)

Esta ferramenta é para fins de pesquisa e auxílio na análise.

*   Os resultados **não são 100% precisos** e devem ser interpretados com cuidado pelo analista.
*   Imagens reais podem ter características que as fazem parecer geradas por IA, e vice-versa.
*   Imagens geradas por IA evoluem constantemente e podem enganar detectores.

## 📧 Contato e Créditos

Desenvolvido por **KGB-LABS**.

*   **GitHub**: [https://github.com/KGB-LABS](https://github.com/KGB-LABS)
*   **Email**: arrudacibersec@proton.me
