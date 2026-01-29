def main():
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")
    st.markdown(f"""
    Dashboard interativo para análise do **Dataset do Mercado Voluntário de Carbono Agrícola** da FAO.  
    *Dados do repositório:* [{GITHUB_USER}/{GITHUB_REPO}](https://github.com/{GITHUB_USER}/{GITHUB_REPO})
    """)

    # ---------- SESSION STATE ----------
    st.session_state.setdefault("data_loaded", False)
    st.session_state.setdefault("show_summary", False)
    st.session_state.setdefault("selected_sheet", None)

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.header("⚙️ Configuração")

        data_source = st.radio(
            "Fonte de dados:",
            ["GitHub Automático", "Upload Manual"]
        )

        if data_source == "GitHub Automático":
            st.info(f"Repositório: {GITHUB_USER}/{GITHUB_REPO}")

            if st.button("🔄 Carregar Dados", type="primary"):
                with st.spinner("Conectando ao GitHub..."):
                    dfs, sheets = load_data_from_github(GITHUB_RAW_URL)
                    if dfs:
                        st.session_state.dataframes = dfs
                        st.session_state.sheets = sheets
                        st.session_state.data_loaded = True
                        st.success("✅ Dados carregados!")
                        st.rerun()
                    else:
                        st.error("❌ Falha ao carregar dados")

        else:
            uploaded_file = st.file_uploader(
                "Upload do Dataset.xlsx",
                type=["xlsx", "xls"]
            )
            if uploaded_file:
                dfs, sheets = load_excel_from_upload(uploaded_file)
                if dfs:
                    st.session_state.dataframes = dfs
                    st.session_state.sheets = sheets
                    st.session_state.data_loaded = True
                    st.success("✅ Arquivo carregado!")
                    st.rerun()

        if st.session_state.data_loaded:
            st.markdown("---")
            st.header("📂 Navegação")

            st.session_state.selected_sheet = st.selectbox(
                "Selecione a aba:",
                st.session_state.sheets
            )

            if st.button("📊 Ver Resumo Geral"):
                st.session_state.show_summary = True

            if st.button("♻️ Limpar Cache"):
                st.cache_data.clear()
                st.rerun()

    # ---------- CONTEÚDO PRINCIPAL ----------
    if not st.session_state.data_loaded:
        st.info("👈 Carregue os dados pela barra lateral.")
        return

    if st.session_state.show_summary:
        create_dashboard_summary(
            st.session_state.dataframes,
            st.session_state.sheets
        )
        st.markdown("---")
        st.session_state.show_summary = False

    sheet = st.session_state.selected_sheet
    df = st.session_state.dataframes[sheet]

    st.header(f"📄 {sheet}")

    total_cells = df.shape[0] * df.shape[1]
    fill_rate = 100 if total_cells == 0 else (
        100 - (df.isnull().sum().sum() / total_cells * 100)
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros", df.shape[0])
    col2.metric("Colunas", df.shape[1])
    col3.metric("Numéricas", len(df.select_dtypes(include=[np.number]).columns))
    col4.metric("Preenchimento", f"{fill_rate:.1f}%")

    create_sheet_specific_analysis(df, sheet)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Dados", "🔍 Análise", "📈 Visualizações", "💾 Exportar"]
    )

    with tab1:
        st.dataframe(df.head(200), use_container_width=True)

    with tab2:
        st.write("### Valores Ausentes")
        missing = df.isnull().mean().mul(100).round(2)
        st.dataframe(missing[missing > 0].sort_values(ascending=False))

    with tab3:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            col = st.selectbox("Coluna numérica:", numeric_cols)
            st.plotly_chart(
                px.histogram(df, x=col, nbins=30),
                use_container_width=True
            )
        else:
            st.info("Sem colunas numéricas.")

    with tab4:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            csv,
            f"{sheet.replace(' ', '_')}.csv",
            "text/csv"
        )

    st.markdown("---")
    st.caption(
        f"FAO Agrifood Carbon Market Dashboard • "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
