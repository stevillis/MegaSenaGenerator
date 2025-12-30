# 🍀 Mega Sena Generator

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.52.2-FF4B4B)
![Pandas](https://img.shields.io/badge/Pandas-2.3.3-003B57)
![SQLite](https://img.shields.io/badge/SQLite-3.45.1-003B57)

Um gerador de números moderno e inteligente para a Mega-Sena, construído com **Python** e **Streamlit**. Este projeto permite gerar palpites, fixar números da sorte, diferenciar apostas reais de sugestões, manter um histórico detalhado e analisar estatísticas com base nos resultados oficiais.

O projeto já vem preparado para importar dados oficiais! Você pode baixar a planilha atualizada em:
👉 [As Loterias - Todos os resultados da Mega Sena](https://asloterias.com.br/download-todos-resultados-mega-sena)

---

## ✨ Funcionalidades

O aplicativo é dividido em 4 módulos principais:

### 1. 🎲 Gerador de Palpites

- **Geração Inteligente:** Crie jogos de 6 dezenas (1 a 60).
- **Números Fixos:** Escolha até 5 números que você *quer* que apareçam no jogo.
- **Múltiplos Jogos:** Gere até 50 combinações de uma vez.
- **Seleção de Apostas:** Após gerar, marque quais jogos você realmente pretende apostar (✅) e quais são apenas sugestões, mantendo seu histórico organizado.

### 2. 📜 Histórico de Palpites

- **Registro Automático:** Todos os jogos (apostas ou sugestões) são salvos no banco de dados local (`db.sqlite3`).
- **Visualização Clara:** Identifique facilmente quais jogos foram marcados como apostas reais.
- **Detalhes:** Data e hora de cada geração, com filtros inteligentes.

### 3. 🏆 Sorteios Oficiais

- **Importação via Excel:** Carregue rapidamente todo o histórico de sorteios usando o arquivo oficial ou nossa planilha modelo (`mega_sena_sorteios.xlsx`).
- **Cadastro Manual:** Opção para registrar o último sorteio manualmente se preferir.
- **Consulta de Números:** Pesquise se seus números da sorte já saíram juntos em algum concurso passado.
- **🔮 Simulador de Aposta (Novo):** Insira um jogo completo e verifique se teria ganhado (Quadra, Quina, Sena) em sorteios passados, com visualização de acertos.
- **Listagem Completa:** Veja todos os concursos cadastrados, com destaque visual para a **Mega da Virada**.

### 4. 📊 Dashboard Estatístico (Análise)

- **Filtro da Virada:** Opção exclusiva para analisar estatísticas considerando apenas os sorteios da Mega da Virada (31/12).
- **Frequência de Números:** Gráficos comparativos entre suas apostas, jogos gerados e a realidade dos sorteios oficiais.
- **Conferência:** Selecione um concurso oficial e verifique automaticamente quantos acertos (Quadra, Quina, Sena) seus jogos gerados teriam feito.
- **Combinações Frequentes:** Descubra quais pares, trincas ou quadras de números saem com mais frequência juntos (Análise de N-grams).

---

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem base.
- **Streamlit**: Interface web interativa e responsiva.
- **Pandas**: Processamento de dados e leitura de Excel.
- **Altair**: Gráficos estatísticos interativos.
- **SQLite**: Banco de dados local para persistência dos dados.

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11 ou superior instalado.

### Passo a Passo

1. **Clone o repositório** (ou baixe os arquivos):

   ```bash
   git clone https://github.com/stevillis/MegaSenaGenerator.git
   cd MegaSenaGenerator
   ```

2. **Instale as dependências**:
   Recomenda-se usar um ambiente virtual (`venv`).

   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação**:

   ```bash
   streamlit run app.py
   ```

4. **Acesse no Navegador**:
   O Streamlit abrirá automaticamente uma aba no seu navegador (geralmente em `http://localhost:8501`).
