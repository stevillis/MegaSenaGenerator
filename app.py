import streamlit as st
import random
import pandas as pd
import sqlite3
import datetime
from collections import Counter
from itertools import combinations
import altair as alt

DB_FILE = "db.sqlite3"


def init_db():
    """
    Initialize the database with the necessary tables.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS generated_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    numbers TEXT,
                    is_bet INTEGER DEFAULT 0
                )"""
    )

    # Migration: Add is_bet column if it doesn't exist
    try:
        c.execute("ALTER TABLE generated_games ADD COLUMN is_bet INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # Column likely already exists
        pass

    c.execute(
        """CREATE TABLE IF NOT EXISTS official_draws (
                    contest_number INTEGER PRIMARY KEY,
                    date TEXT,
                    numbers TEXT
                )"""
    )
    conn.commit()

    return conn


def save_generated_games(conn, games_data):
    """
    Save generated games to the database.
    games_data: List of tuples (numbers_list, is_bet_boolean)
    """
    c = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for numbers, is_bet in games_data:
        numbers_str = ",".join(map(str, sorted(numbers)))
        c.execute(
            "INSERT INTO generated_games (date, numbers, is_bet) VALUES (?, ?, ?)",
            (current_time, numbers_str, 1 if is_bet else 0),
        )

    conn.commit()


def save_official_draw(conn, contest, date, numbers):
    """
    Save official draw to the database.
    """
    c = conn.cursor()
    numbers_str = ",".join(map(str, sorted(numbers)))
    try:
        c.execute(
            "INSERT INTO official_draws (contest_number, date, numbers) VALUES (?, ?, ?)",
            (contest, date.strftime("%Y-%m-%d"), numbers_str),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


@st.cache_data(ttl=600, show_spinner=False)
def get_data(_conn, table_name):
    """
    Get data from the database.
    """
    query = f"SELECT * FROM {table_name}"
    return pd.read_sql_query(query, _conn)


def generate_game_logic(fixed_numbers):
    """
    Generate a game of Mega Sena.
    """
    needed = 6 - len(fixed_numbers)
    possible_numbers = [n for n in range(1, 61) if n not in fixed_numbers]
    random_part = random.sample(possible_numbers, needed)
    full_game = fixed_numbers + random_part
    return sorted(full_game)


def parse_numbers_from_str(numbers_str):
    """
    Parse numbers from a string.
    """
    return [int(n) for n in numbers_str.split(",")]


def is_mega_da_virada(date_val):
    """
    Check if a draw is Mega da Virada (31/12, year >= 2009).
    date_val: Can be a YYYY-MM-DD string or a date object.
    """
    if isinstance(date_val, str):
        try:
            date_obj = datetime.datetime.strptime(date_val, "%Y-%m-%d").date()
        except ValueError:
            return False
    elif isinstance(date_val, (datetime.date, datetime.datetime)):
        date_obj = date_val
    else:
        return False

    return date_obj.month == 12 and date_obj.day == 31 and date_obj.year >= 2009


def display_lottery_balls(numbers, matches=None):
    """
    Display numbers as styled lottery balls.
    matches: A set or list of numbers to highlight.
    """
    if matches is None:
        matches = set()

    html = (
        '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">'
    )
    for num in numbers:
        style = ""
        if num in matches:
            # Highlight style for matches (Gold border/Glow)
            style = "border-color: #FFD700; box-shadow: 0 0 10px #FFD700; transform: scale(1.1);"

        html += f'<div class="lottery-ball" style="{style}">{num:02d}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def page_generator(conn):
    """
    Generate a page for generating numbers.
    """
    st.markdown("## 🎲 Gerador de Números")
    st.markdown(
        """
        Gere palpites inteligentes para a Mega-Sena! 
        Você pode escolher alguns números "da sorte" para fixar, e completaremos o resto.
        Agora você pode selecionar quais jogos realmente deseja apostar antes de salvar no histórico.
        """
    )
    st.markdown("---")

    # Initialize current_games in session state if not present
    if "current_games" not in st.session_state:
        st.session_state.current_games = []

    st.markdown("### Configurações")
    qtd_apostas = st.number_input(
        "Quantos jogos?",
        min_value=1,
        max_value=50,
        value=1,
        help="Defina quantos jogos distintos você deseja gerar de uma vez.",
    )

    fixed_options = list(range(1, 61))
    fixed_selection = st.multiselect(
        "Números Fixos (Opcional)",
        fixed_options,
        help="Escolha até 5 números que OBRIGATORIAMENTE devem aparecer nos jogos gerados.",
        placeholder="Selecione seus números da sorte...",
    )

    st.caption(f"Selecionados: {len(fixed_selection)}/5")

    st.info(
        "💡 **Dica:** Use o Dashboard para ver quais números saem com mais frequência!"
    )

    if len(fixed_selection) > 5:
        st.error(
            "⚠️ Você pode selecionar no máximo **5 números fixos** para um jogo padrão de 6 números."
        )
        return

    st.markdown("<br>", unsafe_allow_html=True)

    # Center the button
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        generate_btn = st.button("✨ GERAR JOGOS ✨", type="primary", width="stretch")

    if generate_btn:
        games_list = []
        for _ in range(qtd_apostas):
            game = generate_game_logic(fixed_selection)
            games_list.append(game)

        # Store in session state instead of saving immediately
        st.session_state.current_games = games_list

    # Display generated games from session state if available
    if st.session_state.current_games:
        st.markdown("---")
        st.subheader("🍀 Seus Palpites Sugeridos:")
        st.markdown(
            "Selecione os jogos que você **realmente** quer apostar. Todos serão salvos, mas marcaremos suas apostas."
        )

        with st.form("bets_form"):
            selections = []
            for i, game in enumerate(st.session_state.current_games, 1):
                c1, c2 = st.columns([0.5, 10])
                with c1:
                    # Using a unique key for each checkbox
                    chk = st.checkbox("", value=True, key=f"bet_chk_{i}")
                    selections.append(chk)
                with c2:
                    st.markdown(f"**Jogo {i}**")
                    display_lottery_balls(game)
                st.markdown(
                    "<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True
                )

            save_submitted = st.form_submit_button(
                "✅ Confirmar e Salvar",
                type="primary",
                width="stretch",
            )

            if save_submitted:
                games_data = []
                count_bets = 0
                for idx, selected in enumerate(selections):
                    game = st.session_state.current_games[idx]
                    games_data.append((game, selected))
                    if selected:
                        count_bets += 1

                save_generated_games(conn, games_data)

                st.success(
                    f"✅ {len(games_data)} jogos salvos! ({count_bets} marcados como aposta)"
                )
                # Clear session state after saving
                st.session_state.current_games = []

                # Clear cache so new games appear in history/dashboard immediately
                get_data.clear()

                # Rerun to update UI
                st.rerun()


def import_official_data_from_excel(conn, file_source):
    """
    Import official draws from an Excel file source (path or buffer).
    Expected columns: "Concurso", "Data", "bola 1", "bola 2", "bola 3", "bola 4", "bola 5", "bola 6"
    """
    try:
        # Load the excel file
        df = pd.read_excel(file_source)
    except FileNotFoundError:
        return 0, 0, f"Arquivo Excel não encontrado: {file_source}"
    except Exception as e:
        return 0, 0, f"Erro ao ler o arquivo Excel: {e}"

    # Required columns check
    required_cols = [
        "Concurso",
        "Data",
        "bola 1",
        "bola 2",
        "bola 3",
        "bola 4",
        "bola 5",
        "bola 6",
    ]
    if not all(col in df.columns for col in required_cols):
        return 0, 0, f"Colunas faltando no Excel. Esperado: {required_cols}"

    added_count = 0
    skipped_count = 0

    for _, row in df.iterrows():
        contest_num = row["Concurso"]
        raw_date = row["Data"]

        # Parse date from dd/mm/yyyy to YYYY-MM-DD
        try:
            if isinstance(raw_date, str):
                date_obj = datetime.datetime.strptime(raw_date, "%d/%m/%Y").date()
            elif isinstance(raw_date, datetime.datetime) or isinstance(
                raw_date, datetime.date
            ):
                date_obj = raw_date
            else:
                date_obj = datetime.date(1900, 1, 1)  # Fallback
        except ValueError:
            skipped_count += 1
            continue

        numbers = []
        for i in range(1, 7):
            val = row[f"bola {i}"]
            try:
                numbers.append(int(val))
            except ValueError:
                pass  # Handle non-integer values?

        if len(numbers) == 6:
            success = save_official_draw(conn, contest_num, date_obj, numbers)
            if success:
                added_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1

    return added_count, skipped_count, None


def page_official_draws(conn):
    """
    Generate a page for official draws.
    Includes Manual Entry, Excel Import, and Search.
    """
    st.markdown("## 🏆 Sorteios e Conferência")
    st.markdown(
        "Mantenha o histórico oficial atualizado e consulte resultados passados."
    )

    tab_register, tab_import, tab_search, tab_simulate, tab_list = st.tabs(
        [
            "📝 Registrar Manual",
            "📂 Importar Excel",
            "🔍 Buscar",
            "🔮 Simular Aposta",
            "📚 Detalhes",
        ]
    )

    # ---------------- TAB 1: Manual Register ----------------
    with tab_register:
        st.markdown("### Registrar Novo Sorteio Oficial")
        st.caption("Insira os dados do último sorteio da Caixa manualmente.")

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            contest_num = st.number_input("Concurso Nº", min_value=1, step=1)
        with c2:
            draw_date = st.date_input("Data do Sorteio")

        with c3:
            drawn_nums = st.multiselect(
                "Selecione as 6 dezenas",
                range(1, 61),
                key="official_input",
            )

        if st.button("💾 Salvar Resultado", width="stretch"):
            if len(drawn_nums) != 6:
                st.error("⚠️ Um jogo da Mega-Sena tem exatamente **6 números**.")
            else:
                success = save_official_draw(conn, contest_num, draw_date, drawn_nums)
                if success:
                    st.toast(f"Sorteio {contest_num} salvo com sucesso!", icon="✅")
                    st.success("Sorteio registrado!")
                    # Clear cache to reflect new data
                    get_data.clear()
                else:
                    st.error(f"O concurso {contest_num} já está cadastrado.")

    with tab_import:
        st.markdown("### Importar Base de Dados Recente")
        st.markdown(
            "Importe dados do arquivo `mega_sena_sorteios.xlsx` ou faça upload de uma planilha."
        )

        uploaded_file = st.file_uploader(
            "Carregar arquivo Excel (.xlsx)", type=["xlsx"]
        )

        # Defines the source
        source_to_use = None
        if uploaded_file is not None:
            source_to_use = uploaded_file
            btn_label = "📂 Importar do Upload"
        else:
            source_to_use = "mega_sena_sorteios.xlsx"
            btn_label = "📂 Importar do Arquivo Local (Padrão)"

        if st.button(btn_label, type="primary"):
            with st.spinner("Lendo arquivo e atualizando banco de dados..."):
                added, skipped, error = import_official_data_from_excel(
                    conn, source_to_use
                )

            if error:
                st.error(f"Erro na importação: {error}")
            else:
                st.success(
                    f"Importação Concluída! ✅ Adicionados: {added} | ⏭️ Ignorados/Duplicados: {skipped}"
                )
                if added > 0:
                    st.toast(f"{added} novos sorteios importados!")
                    # Clear cache to reflect new data immediately
                    get_data.clear()

    # ---------------- TAB 3: Search Numbers ----------------
    with tab_search:
        st.markdown("### 🔍 Consultar Dezenas Sorteadas")
        st.markdown("Descubra em quais concursos seus números da sorte já saíram.")

        search_nums = st.multiselect(
            "Selecione os números para pesquisar:",
            options=range(1, 61),
            placeholder="Ex: 10, 25, 60...",
        )

        search_mode = st.radio(
            "Modo de Busca:",
            ["Contém TODOS os números", "Contém PELO MENOS UM dos números"],
            index=0,
        )

        if search_nums:
            df = get_data(conn, "official_draws")

            if df.empty:
                st.warning(
                    "Sem dados oficiais para pesquisar. Importe ou registre sorteios primeiro."
                )
            else:
                results = []
                search_set = set(search_nums)

                # Filter logic
                for _, row in df.iterrows():
                    draw_nums = set(parse_numbers_from_str(row["numbers"]))

                    match = False
                    intersection = draw_nums.intersection(search_set)

                    if search_mode == "Contém TODOS os números":
                        if search_set.issubset(draw_nums):
                            match = True
                    else:  # ANY
                        if intersection:
                            match = True

                    if match:
                        results.append(
                            {
                                "Concurso": row["contest_number"],
                                "Data": row["date"],
                                "Dezenas": row[
                                    "numbers"
                                ],  # Keep as string for display or parse later
                                "Coincidências": sorted(list(intersection)),
                                "Tipo": (
                                    "⭐ Mega da Virada"
                                    if is_mega_da_virada(row["date"])
                                    else "Regular"
                                ),
                            }
                        )

                if results:
                    st.subheader(
                        f"Encontrados {len(results)} sorteios correspondentes:"
                    )
                    df_res = pd.DataFrame(results)
                    # Sort desc by contest
                    df_res = df_res.sort_values(by="Concurso", ascending=False)

                    st.dataframe(
                        df_res,
                        column_config={
                            "Coincidências": st.column_config.ListColumn(
                                "Números Encontrados"
                            )
                        },
                        hide_index=True,
                        width="stretch",
                    )
                else:
                    st.info("Nenhum sorteio encontrado com esses critérios.")

                    st.info("Nenhum sorteio encontrado com esses critérios.")

    # ---------------- TAB 4: Simulate Bet ----------------
    with tab_simulate:
        st.markdown("### 🔮 Simular Aposta (Tira-Teima)")
        st.markdown(
            "Escolha seus números e veja se você teria ganhado em algum sorteio passado!"
        )

        sim_nums = st.multiselect(
            "Escolha seus números (6 a 15):",
            range(1, 61),
            key="sim_nums_check",
            max_selections=15,
        )

        st.caption(f"Números selecionados: {len(sim_nums)}")

        if st.button(
            "🚀 Consultar Resultados Passados", type="primary", use_container_width=True
        ):
            if len(sim_nums) < 6:
                st.error("⚠️ Selecione pelo menos **6 números** para simular.")
            else:
                df = get_data(conn, "official_draws")
                if df.empty:
                    st.warning("⚠️ Sem dados oficiais para consultar.")
                else:
                    user_set = set(sim_nums)
                    results = []

                    # Iterate over all draws
                    for _, row in df.iterrows():
                        draw_nums = parse_numbers_from_str(row["numbers"])
                        draw_set = set(draw_nums)

                        # Calculate intersection (hits)
                        intersection = user_set.intersection(draw_set)
                        hits_count = len(intersection)

                        # We care about 3 or more hits usually (Quadra, Quina, Sena + Terno for curiosity)
                        if hits_count >= 3:
                            results.append(
                                {
                                    "contest": row["contest_number"],
                                    "date": row["date"],
                                    "draw_nums": sorted(draw_nums),
                                    "hits": hits_count,
                                    "matched_nums": intersection,
                                }
                            )

                    if not results:
                        st.info(
                            "📉 Que pena! Você não teria feito nem a Quadra (nem Terno) em nenhum sorteio cadastrado."
                        )
                    else:
                        # Sort by hits (desc), then contest (desc)
                        results.sort(
                            key=lambda x: (x["hits"], x["contest"]), reverse=True
                        )

                        st.success(
                            f"🎉 Encontramos {len(results)} sorteios onde você teria acertado 3 ou mais números!"
                        )

                        for res in results:
                            # Card styling
                            hits = res["hits"]

                            # Determine label color
                            if hits == 6:
                                label_txt = "💎 SENA (6 acertos)"
                                label_color = "#4CAF50"  # Green
                            elif hits == 5:
                                label_txt = "🌟 QUINA (5 acertos)"
                                label_color = "#9C27B0"  # Purple
                            elif hits == 4:
                                label_txt = "🍀 QUADRA (4 acertos)"
                                label_color = "#2196F3"  # Blue
                            else:
                                label_txt = "🎲 TERNO (3 acertos)"
                                label_color = "#FF9800"  # Orange

                            # Start building HTML string
                            # We use a single string to avoid Markdown indentation issues that treat HTML as code blocks
                            card_html = f"""
                            <div style="background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {label_color};">
                                <h4 style="margin: 0; color: {label_color};">{label_txt}</h4>
                                <p style="margin: 5px 0 10px 0; font-size: 0.9em; opacity: 0.8;">
                                    Concurso <b>{res['contest']}</b> ({res['date']})
                                </p>
                                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                            """

                            # Render balls manually
                            for num in res["draw_nums"]:
                                if num in res["matched_nums"]:
                                    # Hit (Green)
                                    bg_style = "radial-gradient(circle at 30% 30%, #4CAF50, #1b5e20)"
                                    border = "2px solid #fff"
                                    opacity = "1"
                                else:
                                    # Miss (Red)
                                    bg_style = "radial-gradient(circle at 30% 30%, #D32F2F, #B71C1C)"
                                    border = "1px solid rgba(255,255,255,0.5)"
                                    opacity = "0.9"

                                # Append ball HTML (no indentation to be safe)
                                card_html += f'<div style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: {bg_style}; color: white; font-weight: bold; font-size: 16px; border: {border}; opacity: {opacity}; box-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{num:02d}</div>'

                            card_html += "</div></div>"

                            st.markdown(card_html, unsafe_allow_html=True)

    with tab_list:
        st.subheader("📚 Histórico Completo Oficial")
        df = get_data(conn, "official_draws")
        if not df.empty:
            df = df.sort_values(by="contest_number", ascending=False)

            # Add a 'Type' column for display
            df["type_display"] = df["date"].apply(
                lambda d: "⭐ Mega da Virada" if is_mega_da_virada(d) else "Regular"
            )

            st.dataframe(
                df,
                column_config={
                    "contest_number": "Concurso",
                    "date": "Data",
                    "numbers": "Dezenas",
                    "type_display": "Tipo",
                },
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("Nenhum sorteio oficial registrado ainda.")


def page_history(conn):
    """
    Generate a page for viewing generated games history.
    """
    st.markdown("## 📜 Histórico de Palpites")
    st.markdown("Veja todos os jogos que você já gerou nesta ferramenta.")

    df = get_data(conn, "generated_games")
    if not df.empty:
        df = df.sort_values(by="id", ascending=False)

        # Handle is_bet column visibility
        if "is_bet" in df.columns:
            df["is_bet"] = (
                df["is_bet"]
                .fillna(0)
                .apply(lambda x: "✅ Aposta" if x == 1 else "🎲 Sugestão")
            )
        else:
            df["is_bet"] = (
                "🎲 Sugestão"  # Fallback for old data without column if migration failed silently
            )

        st.dataframe(
            df,
            column_config={
                "id": "ID",
                "date": "Data Gerada",
                "numbers": "Números Gerados",
                "is_bet": "Tipo",
            },
            hide_index=True,
            width="stretch",
        )

        st.markdown(f"**Total de jogos gerados:** {len(df)}")
    else:
        st.warning("Seu histórico está vazio. Vá ao **Gerador** para começar!")


def page_dashboard(conn):
    """
    Generate a dashboard with statistics.
    """
    st.markdown("## 📊 Análise Estatística")

    df_gen = get_data(conn, "generated_games")

    # Initialize lists
    bets_nums = []
    ignored_nums = []

    if not df_gen.empty:
        # Handle backward compatibility or missing column
        if "is_bet" not in df_gen.columns:
            df_gen["is_bet"] = 0

        # Split into bets and ignored
        df_bets = df_gen[df_gen["is_bet"] == 1]
        df_ignored = df_gen[df_gen["is_bet"] == 0]

        for nums_str in df_bets["numbers"]:
            bets_nums.extend(parse_numbers_from_str(nums_str))

        for nums_str in df_ignored["numbers"]:
            ignored_nums.extend(parse_numbers_from_str(nums_str))

    df_off = get_data(conn, "official_draws")

    # Filter for Mega da Virada
    st.sidebar.markdown("### ⚙️ Filtros do Dashboard")
    filter_virada = st.sidebar.checkbox(
        "⭐ Apenas Mega da Virada",
        help="Analise apenas os sorteios especiais de 31/12.",
    )

    if filter_virada:
        # Apply filter
        # Ensure we can check the date column
        if not df_off.empty:
            # We need to apply the function row by row
            mask = df_off["date"].apply(is_mega_da_virada)
            df_off = df_off[mask]
            st.info(f"🔍 Analisando apenas {len(df_off)} sorteios da Mega da Virada!")

    all_off_nums = []
    if not df_off.empty:
        for nums_str in df_off["numbers"]:
            all_off_nums.extend(parse_numbers_from_str(nums_str))

    # Top Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jogos Gerados", len(df_gen))
    m2.metric("Apostas Realizadas", len(df_gen[df_gen["is_bet"] == 1]))
    m3.metric("Sorteios Oficiais", len(df_off))

    common_bet = Counter(bets_nums).most_common(1)[0] if bets_nums else ("-", 0)
    m4.metric("Nº Mais Apostado", f"{common_bet[0]}", f"{common_bet[1]}x")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        [
            "🔥 Dezenas Quentes",
            "✅ Conferência",
            "🔗 Combinações Frequentes",
        ]
    )

    with tab1:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("### 🟢 Suas Apostas")
            if bets_nums:
                df_counts = pd.DataFrame(
                    Counter(bets_nums).most_common(10), columns=["Dezena", "Frequência"]
                )
                chart = (
                    alt.Chart(df_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("Dezena:O", sort="-y", title="Dezena"),
                        y=alt.Y("Frequência", title="Frequência"),
                        tooltip=["Dezena", "Frequência"],
                        color=alt.value("#4CAF50"),
                    )
                )
                st.altair_chart(chart, width="stretch")
            else:
                st.caption("Sem dados de apostas.")

        with c2:
            st.markdown("### 🟡 Gerados (Ignorados)")
            if ignored_nums:
                df_counts = pd.DataFrame(
                    Counter(ignored_nums).most_common(10),
                    columns=["Dezena", "Frequência"],
                )
                chart = (
                    alt.Chart(df_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("Dezena:O", sort="-y", title="Dezena"),
                        y=alt.Y("Frequência", title="Frequência"),
                        tooltip=["Dezena", "Frequência"],
                        color=alt.value("#FFC107"),
                    )
                )
                st.altair_chart(chart, width="stretch")
            else:
                st.caption("Sem dados de jogos ignorados.")

        with c3:
            st.markdown("### 🔵 Realidade (Oficial)")
            if all_off_nums:
                df_counts = pd.DataFrame(
                    Counter(all_off_nums).most_common(10),
                    columns=["Dezena", "Frequência"],
                )
                chart = (
                    alt.Chart(df_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("Dezena:O", sort="-y", title="Dezena"),
                        y=alt.Y("Frequência", title="Frequência"),
                        tooltip=["Dezena", "Frequência"],
                        color=alt.value("#2196F3"),
                    )
                )
                st.altair_chart(chart, width="stretch")
            else:
                st.caption("Sem dados oficiais.")

    with tab2:
        st.markdown("### 🔎 Conferência de Jogos")
        st.markdown(
            "Verifique como seus jogos teriam se saído em um sorteio específico."
        )

        if df_off.empty:
            st.warning(
                "Cadastre sorteios oficiais na aba 'Sorteios Oficiais' para usar esta função."
            )
        elif df_gen.empty:
            st.warning("Gere jogos na aba 'Gerador' para conferir.")
        else:
            # Dropdown to select official draw
            # Sort by date desc
            df_off_sorted = df_off.sort_values(by="contest_number", ascending=False)

            draw_options = df_off_sorted.to_dict("records")

            selected_draw_data = st.selectbox(
                "Selecione o Sorteio Oficial para conferir:",
                options=draw_options,
                format_func=lambda x: f"Concurso {x['contest_number']} ({x['date']}) - {x['numbers']}",
            )

            min_hits = st.radio(
                "Filtrar por Mínimo de Acertos:",
                options=[1, 2, 3, 4, 5, 6],
                horizontal=True,
                format_func=lambda x: "Todos" if x == 0 else f"{x}+",
            )

            if selected_draw_data:
                draw_nums = set(parse_numbers_from_str(selected_draw_data["numbers"]))

                st.markdown(
                    f"**Dezenas do Concurso {selected_draw_data['contest_number']}:**"
                )
                display_lottery_balls(sorted(list(draw_nums)))
                st.markdown("---")

                # Process games and calculate hits
                results = []
                for idx, row in df_gen.iterrows():
                    game_nums = parse_numbers_from_str(row["numbers"])
                    game_set = set(game_nums)
                    matches = game_set.intersection(draw_nums)
                    hits = len(matches)

                    if hits >= min_hits:
                        results.append(
                            {
                                "id": row["id"],
                                "date": row["date"],
                                "numbers": game_nums,
                                "matches": matches,
                                "hits": hits,
                                "is_bet": row.get("is_bet", 0),
                            }
                        )

                # Sort by hits (desc), then by bet status (bets first)
                results.sort(key=lambda x: (x["hits"], x["is_bet"]), reverse=True)

                st.caption(f"Exibindo {len(results)} jogos com {min_hits}+ acertos.")

                for res in results:
                    col_info, col_balls = st.columns([2, 5])

                    with col_info:
                        tag = "✅ APOSTA" if res["is_bet"] == 1 else "🎲 Sugestão"
                        tag_color = "green" if res["is_bet"] == 1 else "grey"
                        st.markdown(f":{tag_color}[{tag}]")
                        st.caption(f"Gerado em: {res['date']}")

                        hits_color = "red"
                        if res["hits"] >= 4:
                            hits_color = "green"
                        elif res["hits"] == 3:
                            hits_color = "orange"

                        st.markdown(f"**Acertos: :{hits_color}[{res['hits']}]**")

                    with col_balls:
                        display_lottery_balls(res["numbers"], matches=res["matches"])

                    st.divider()

    with tab3:
        st.markdown("### 🔗 Frequência de Combinações")
        st.markdown(
            "Descubra quais grupos de números costumam sair juntos com mais frequência nos sorteios oficiais."
        )

        if not all_off_nums:
            st.warning(
                "Sem dados oficiais para analisar. Importe ou registre sorteios na aba 'Sorteios Oficiais'."
            )
        else:
            # Prepare data: list of lists of numbers
            official_draws_list = []
            if not df_off.empty:
                for nums_str in df_off["numbers"]:
                    official_draws_list.append(parse_numbers_from_str(nums_str))

            # Selector for N-gram size
            ngram_size = st.radio(
                "Tamanho da Combinação:",
                options=[2, 3, 4, 5],
                format_func=lambda x: {
                    2: "Duque (2 números)",
                    3: "Terno (3 números)",
                    4: "Quadra (4 números)",
                    5: "Quina (5 números)",
                }[x],
                horizontal=True,
            )

            # Calculation
            all_ngrams = []
            for draw in official_draws_list:
                # Ensure sorted for consistent tuples
                draw_sorted = sorted(draw)
                for combo in combinations(draw_sorted, ngram_size):
                    all_ngrams.append(combo)

            if all_ngrams:
                ngram_counts = Counter(all_ngrams).most_common(15)

                # Format for display
                data_list = []
                for combo, count in ngram_counts:
                    combo_str = ", ".join([f"{n:02d}" for n in combo])
                    data_list.append({"Combinação": combo_str, "Frequência": count})

                df_ngrams = pd.DataFrame(data_list)

                # Chart
                chart_ngrams = (
                    alt.Chart(df_ngrams)
                    .mark_bar()
                    .encode(
                        x=alt.X("Combinação", sort="-y", title="Combinação"),
                        y=alt.Y("Frequência", title="Vezes Sorteada"),
                        tooltip=["Combinação", "Frequência"],
                        color=alt.value("#673AB7"),  # Deep Purple
                    )
                )

                st.altair_chart(chart_ngrams, width="stretch")

                st.markdown("#### Detalhes")
                st.dataframe(df_ngrams, width="stretch", hide_index=True)
            else:
                st.info(
                    "Nenhuma combinação encontrada com esse tamanho (possivelmente dados insuficientes)."
                )


def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(
        page_title="Mega-Sena Generator",
        page_icon="🍀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject Custom CSS for Premium Look
    st.markdown(
        """
        <style>
        /* Button Styling - Adaptive to Theme */
        div.stButton > button {
            border-radius: 20px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        
        /* Lottery Ball Style - Always Green/White */
        .lottery-ball {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #4CAF50, #1b5e20);
            color: white;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            border: 2px solid #fff;
        }
        
        /* Headings - Adaptive */
        h1, h2, h3 {
            color: #2E7D32 !important;
        }
        @media (prefers-color-scheme: dark) {
            h1, h2, h3 {
                color: #66BB6A !important;
            }
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    conn = init_db()

    with st.sidebar:
        st.title("🍀 Mega-Sena")
        st.markdown("*Gerador de Palpites & Estatísticas*")

        menu_options = {
            "Gerador": "🎲",
            "Histórico": "📜",
            "Dashboard": "📊",
            "Sorteios Oficiais": "🏆",
        }

        selected_label = st.radio(
            "Navegação",
            list(menu_options.keys()),
            format_func=lambda x: f"{menu_options[x]} {x}",
        )

        st.markdown("---")
        st.info(
            "Dica: Atualize os 'Sorteios Oficiais' regularmente para melhorar o comparativo!"
        )

    if selected_label == "Gerador":
        page_generator(conn)
    elif selected_label == "Histórico":
        page_history(conn)
    elif selected_label == "Dashboard":
        page_dashboard(conn)
    elif selected_label == "Sorteios Oficiais":
        page_official_draws(conn)


if __name__ == "__main__":
    main()
