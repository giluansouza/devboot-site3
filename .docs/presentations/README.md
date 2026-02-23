# Sistema de Apresentações Institucionais

Este diretório contém os artefatos para a criação de apresentações comerciais e institucionais do FrotasPro.

A abordagem utiliza HTML/CSS como fonte da verdade, permitindo controle de versão, consistência e reusabilidade. A estratégia completa está documentada em `strategy.md`.

## Como Criar uma Nova Apresentação

1.  **Copie o Template:** Não modifique o `template.html` diretamente. Crie uma cópia para a sua nova apresentação.
    ```bash
    cp template.html minha-nova-apresentacao.html
    ```
    Para uma versão em PDF (portrait), use:
    ```bash
    cp template-pdf-portrait.html minha-apresentacao-portrait.html
    ```
    Já existe um template voltado para empresas privadas em `template-pdf-portrait-empresas.html`.
2.  **Edite o Conteúdo:** Modifique o arquivo `.html` para adequar a narrativa, alterar textos, substituir placeholders de imagens e customizar para o público-alvo (ex: empresa, unidade/filial, prefeitura, etc.).

## Como Exportar para PDF (Processo Padrão)

A exportação para PDF é um passo crucial e deve ser feita de forma consistente para garantir a qualidade visual.

1.  **Abra o arquivo HTML no Google Chrome** (ou outro navegador baseado em Chromium).
2.  Abra a caixa de diálogo de Impressão (`Ctrl+P` ou `Cmd+P`).
3.  Configure as seguintes opções **exatamente** como descrito:
    *   **Destino:** Salvar como PDF
    *   **Layout:** Paisagem (para `template.html`) / Retrato (para `template-pdf-portrait*.html`)
    *   **Mais definições**
        *   **Tamanho do papel:** A4 (ou o padrão desejado, mas seja consistente)
        *   **Páginas por folha:** 1
        *   **Margens:** Nenhuma
        *   **Escala:** Padrão (ou 100%)
        *   **Opções:**
            *   [x] Gráficos de segundo plano

4.  Clique em **Salvar**. Nomeie o arquivo PDF de forma descritiva (ex: `Apresentacao_FrotasPro_Cliente_Exemplo_2026-01-24.pdf`).

Manter este processo garante que todas as apresentações exportadas tenham a mesma aparência profissional e padronizada.
