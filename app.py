# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import warnings
import requests
from io import BytesIO
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="FAO Agrifood Carbon Market Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL do seu dataset no GitHub
GITHUB_USER = "tco2eq_v3"
GITHUB_REPO = "tco2eq_v3"  # Assumindo que o repositório tem o mesmo nome
DATASET_PATH = "Dataset.xlsx"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{DATASET_PATH}"

# Cache para dados (24 horas)
@st.cache_data(ttl=86400, show_spinner="Carregando dados do GitHub...")
def load_data_from_github(url):
    """Carrega dados diretamente do GitHub"""
    try:
        # Baixar o arquivo
        response = requests.get(url)
        response.raise_for_status()
        
        # Ler o Excel
        excel_file = pd.ExcelFile(BytesIO(response.content))
        sheets = excel_file.sheet_names
        dataframes = {}
        
        for sheet in sheets:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            dataframes[sheet] = df
        
        return dataframes, sheets
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do GitHub: {e}")
        return {}, []

@st.cache_data
def load_excel_from_upload(file):
    """Carrega dados de upload manual"""
    try:
        excel_file = pd.ExcelFile(file)
        sheets = excel_file.sheet_names
        dataframes = {}
        
        for sheet in sheets:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            dataframes[sheet] = df
        
        return dataframes, sheets
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return {}, []

# Funções de análise otimizadas
def analyze_sheet_structure(df, sheet_name):
    """Analisa a estrutura da aba"""
    analysis = {
        'sheet_name': sheet_name,
        'rows': df.shape[0],
        'columns': df.shape[1],
        'numeric_cols': len(df.select_dtypes(include=[np.number]).columns),
        'text_cols': len(df.select_dtypes(include=['object']).columns),
        'null_percentage': (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100),
        'sample_columns': df.columns.tolist()[:5]
    }
    return analysis

def create_dashboard_summary(dataframes, sheets):
    """Cria resumo geral do dataset"""
    st.subheader("📊 Resumo Geral do Dataset")
    
    summary_data = []
    for sheet in sheets:
        if sheet in dataframes:
            df = dataframes[sheet]
            analysis = analyze_sheet_structure(df, sheet)
            summary_data.append(analysis)
    
    summary_df = pd.DataFrame(summary_data)
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Abas", len(sheets))
    with col2:
        total_rows = summary_df['rows'].sum()
        st.metric("Total de Registros", f"{total_rows:,}")
    with col3:
        total_cols = summary_df['columns'].sum()
        st.metric("Total de Colunas", total_cols)
    with col4:
        avg_fill = 100 - summary_df['null_percentage'].mean()
        st.metric("Dados Preenchidos (média)", f"{avg_fill:.1f}%")
    
    # Tabela de resumo
    st.dataframe(
        summary_df[['sheet_name', 'rows', 'columns', 'numeric_cols', 'null_percentage']]
        .rename(columns={
            'sheet_name': 'Aba',
            'rows': 'Linhas',
            'columns': 'Colunas',
            'numeric_cols': 'Col. Numéricas',
            'null_percentage': '% Nulos'
        }),
        use_container_width=True
    )

def create_sheet_specific_analysis(df, sheet_name):
    """Análise específica por tipo de aba"""
    
    # Aba de Standards
    if sheet_name == '1. Standards':
        st.subheader("🏆 Análise de Padrões de Carbono")
        
        if 'Name of standard/registry/platform' in df.columns:
            standards_info = df[['Name of standard/registry/platform', 'Total registered projects']].copy()
            standards_info = standards_info.dropna()
            
            if not standards_info.empty:
                try:
                    standards_info['Total registered projects'] = pd.to_numeric(
                        standards_info['Total registered projects'], errors='coerce'
                    )
                    standards_info = standards_info.dropna()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(
                            standards_info.sort_values('Total registered projects', ascending=False).head(10),
                            x='Name of standard/registry/platform',
                            y='Total registered projects',
                            title="Top 10 Padrões por Projetos",
                            color='Total registered projects',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        total_projects = standards_info['Total registered projects'].sum()
                        avg_projects = standards_info['Total registered projects'].mean()
                        
                        st.metric("Total de Projetos (estimado)", f"{total_projects:,.0f}")
                        st.metric("Média por Padrão", f"{avg_projects:,.0f}")
                        
                        # Lista de padrões
                        st.write("### 📋 Lista de Padrões")
                        for idx, row in standards_info.iterrows():
                            st.write(f"**{row['Name of standard/registry/platform']}**: {row['Total registered projects']:,.0f} projetos")
                
                except Exception as e:
                    st.info(f"Não foi possível analisar os dados de padrões: {e}")
    
    # Aba de Projetos (4, 5, 6)
    elif sheet_name in ['4. Agriculture', '5. Agroforestry-AR & Grassland', '6. Energy and Other ']:
        st.subheader(f"🌱 Análise de Projetos - {sheet_name}")
        
        # Identificar colunas de créditos
        credit_cols = [col for col in df.columns if 'credit' in str(col).lower() and 'issued' in str(col).lower()]
        
        if credit_cols:
            try:
                # Encontrar a melhor coluna de créditos
                credit_col = credit_cols[0]
                if df[credit_col].dtype in [np.int64, np.float64]:
                    credits_data = df[credit_col].dropna()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_credits = credits_data.sum()
                        st.metric("Total de Créditos", f"{total_credits:,.0f}")
                    
                    with col2:
                        avg_credits = credits_data.mean()
                        st.metric("Média por Projeto", f"{avg_credits:,.0f}")
                    
                    with col3:
                        max_credits = credits_data.max()
                        st.metric("Máximo", f"{max_credits:,.0f}")
                    
                    # Distribuição
                    fig = px.histogram(
                        credits_data,
                        nbins=30,
                        title="Distribuição de Créditos",
                        labels={'value': 'Créditos', 'count': 'Número de Projetos'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            except:
                pass
        
        # Análise por tipo de registro
        if 'Unnamed: 2' in df.columns:
            registry_counts = df['Unnamed: 2'].value_counts()
            
            fig = px.pie(
                values=registry_counts.values,
                names=registry_counts.index,
                title="Distribuição por Tipo de Registro",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Aba 7 (Plan Vivo, etc.)
    elif sheet_name == '7. Plan Vivo, Acorn, Social C':
        st.subheader("🌍 Projetos de Pequenos Produtores")
        
        if 'Standard' in df.columns and 'Issued credits' in df.columns:
            # Análise por padrão
            standard_analysis = df.groupby('Standard').agg({
                'Issued credits': 'sum',
                'Project name': 'count'
            }).reset_index()
            
            standard_analysis = standard_analysis.rename(columns={
                'Project name': 'Total Projetos',
                'Issued credits': 'Total Créditos'
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    standard_analysis,
                    x='Standard',
                    y='Total Créditos',
                    title='Créditos por Padrão',
                    color='Total Projetos',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(
                    standard_analysis,
                    values='Total Projetos',
                    names='Standard',
                    title='Distribuição de Projetos',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Métricas
            total_credits = df['Issued credits'].sum()
            total_projects = df.shape[0]
            
            st.metric("Total de Créditos Emitidos", f"{total_credits:,.0f}")
            st.metric("Total de Projetos", total_projects)
    
    # Aba 8 (Puro.earth)
    elif sheet_name == '8. Puro.earth':
        st.subheader("🔥 Projetos de Biochar")
        
        # Identificar colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            # Supondo que as colunas de 2019-2023 são as primeiras numéricas
            year_cols = numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols
            
            # Calcular totais por ano
            yearly_totals = {}
            for col in year_cols:
                yearly_totals[col] = df[col].sum()
            
            yearly_df = pd.DataFrame({
                'Ano': list(yearly_totals.keys()),
                'Total': list(yearly_totals.values())
            })
            
            fig = px.line(
                yearly_df,
                x='Ano',
                y='Total',
                title='Evolução de Créditos por Ano',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Aba 9 (Nori and BCarbon)
    elif sheet_name == '9. Nori and BCarbon':
        st.subheader("🌳 Projetos em Países Desenvolvidos")
        
        if 'Standard' in df.columns and 'Issued credits' in df.columns:
            # Comparação entre padrões
            comparison = df.groupby('Standard')['Issued credits'].agg(['sum', 'mean', 'count']).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📊 Comparação entre Padrões")
                st.dataframe(comparison, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    comparison,
                    x='Standard',
                    y='sum',
                    title='Total de Créditos por Padrão',
                    color='count',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)

def main():
    # Título principal
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")
    st.markdown(f"""
    Dashboard interativo para análise do **Dataset do Mercado Voluntário de Carbono Agrícola** da FAO.
    *Dados carregados automaticamente do repositório: [{GITHUB_USER}/{GITHUB_REPO}](https://github.com/{GITHUB_USER}/{GITHUB_REPO})*
    """)
    
    # Inicializar session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuração")
        
        # Opção de fonte de dados
        data_source = st.radio(
            "Fonte de dados:",
            ["GitHub Automático", "Upload Manual"],
            index=0
        )
        
        dataframes = {}
        sheets = []
        
        if data_source == "GitHub Automático":
            st.info(f"Carregando de: {GITHUB_USER}/{GITHUB_REPO}")
            
            if st.button("🔄 Carregar Dados", type="primary") or not st.session_state.data_loaded:
                with st.spinner("Conectando ao GitHub..."):
                    dataframes, sheets = load_data_from_github(GITHUB_RAW_URL)
                    if dataframes:
                        st.session_state.data_loaded = True
                        st.session_state.dataframes = dataframes
                        st.session_state.sheets = sheets
                        st.success("✅ Dados carregados!")
                    else:
                        st.error("❌ Falha ao carregar dados")
        
        else:  # Upload Manual
            uploaded_file = st.file_uploader(
                "Faça upload do Dataset.xlsx",
                type=['xlsx', 'xls'],
                help="Caso o carregamento automático falhe"
            )
            
            if uploaded_file:
                with st.spinner("Processando arquivo..."):
                    dataframes, sheets = load_excel_from_upload(uploaded_file)
                    if dataframes:
                        st.session_state.data_loaded = True
                        st.session_state.dataframes = dataframes
                        st.session_state.sheets = sheets
                        st.success("✅ Arquivo processado!")
        
        st.markdown("---")
        
        # Navegação (se dados carregados)
        if st.session_state.data_loaded:
            st.header("📂 Navegação")
            
            selected_sheet = st.selectbox(
                "Selecione a aba para análise:",
                st.session_state.sheets,
                index=1 if len(st.session_state.sheets) > 1 else 0
            )
            
            st.markdown("---")
            st.header("🚀 Ações Rápidas")
            
            if st.button("📊 Ver Resumo Geral"):
                st.session_state.show_summary = True
            
            if st.button("🔄 Atualizar Cache"):
                st.cache_data.clear()
                st.rerun()
            
            return selected_sheet
    
    # Conteúdo principal
    if not st.session_state.get('data_loaded', False):
        # Tela inicial
        st.info("👈 **Selecione a fonte de dados na barra lateral e clique em 'Carregar Dados'**")
        
        # Layout informativo
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📋 Sobre o Dataset
            
            **Agrifood Voluntary Carbon Market Dataset** (FAO, 2025)
            
            • **10 abas** organizadas tematicamente  
            • **1,000+ projetos** de carbono analisados  
            • **1996-2023** dados históricos  
            • **Padrões globais** (Verra, Gold Standard, etc.)  
            • **Metodologias** de cálculo documentadas  
            • **Plataformas** de MRV e monitoramento
            """)
            
            st.image("https://www.fao.org/assets/images/FAO-logo-white.svg", width=200)
        
        with col2:
            st.markdown("""
            ### 🎯 Análises Disponíveis
            
            **1. Padrões & Certificações**  
            - Comparação entre padrões  
            - Projetos registrados  
            - Escopos e metodologias  
            
            **2. Projetos por Categoria**  
            - Agricultura (758 projetos)  
            - Agroflorestal (170 projetos)  
            - Energia (29 projetos)  
            
            **3. Plataformas Especializadas**  
            - Plan Vivo, Acorn, Social Carbon  
            - Puro.earth (biochar)  
            - Nori, BCarbon  
            
            **4. Metodologias**  
            - 89 metodologias documentadas  
            - Análise por tipo e padrão
            """)
        
        # Botão para carregar automaticamente
        if st.button("🚀 Carregar Dados Automaticamente", type="primary"):
            with st.spinner("Conectando ao GitHub..."):
                dataframes, sheets = load_data_from_github(GITHUB_RAW_URL)
                if dataframes:
                    st.session_state.data_loaded = True
                    st.session_state.dataframes = dataframes
                    st.session_state.sheets = sheets
                    st.rerun()
                else:
                    st.error("Não foi possível carregar os dados. Tente o upload manual.")
        
        return None
    
    else:
        # Dados carregados - mostrar conteúdo
        selected_sheet = main()
        
        if selected_sheet:
            df = st.session_state.dataframes[selected_sheet]
            sheets = st.session_state.sheets
            
            # Mostrar resumo geral se solicitado
            if st.session_state.get('show_summary', False):
                create_dashboard_summary(st.session_state.dataframes, sheets)
                st.markdown("---")
            
            # Cabeçalho da aba
            st.header(f"📄 {selected_sheet}")
            
            # Métricas rápidas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Registros", df.shape[0])
            
            with col2:
                st.metric("Colunas", df.shape[1])
            
            with col3:
                numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                st.metric("Colunas Numéricas", numeric_cols)
            
            with col4:
                fill_rate = 100 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
                st.metric("Dados Preenchidos", f"{fill_rate:.1f}%")
            
            # Análise específica da aba
            create_sheet_specific_analysis(df, selected_sheet)
            
            # Tabs para análise detalhada
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Dados", "🔍 Análise", "📈 Visualizações", "💾 Exportar"])
            
            with tab1:
                # Visualização dos dados
                st.subheader("Visualização dos Dados")
                
                # Filtros
                col1, col2 = st.columns(2)
                
                with col1:
                    columns_to_show = st.multiselect(
                        "Colunas para mostrar:",
                        df.columns.tolist(),
                        default=df.columns.tolist()[:min(8, len(df.columns))]
                    )
                
                with col2:
                    rows_to_show = st.slider(
                        "Linhas:",
                        min_value=10,
                        max_value=min(500, df.shape[0]),
                        value=100,
                        step=10
                    )
                
                # Mostrar dados
                if columns_to_show:
                    display_df = df[columns_to_show].head(rows_to_show)
                else:
                    display_df = df.head(rows_to_show)
                
                st.dataframe(display_df, use_container_width=True, height=400)
            
            with tab2:
                # Análise detalhada
                st.subheader("Análise Detalhada")
                
                # Valores ausentes
                st.write("### 🔍 Valores Ausentes")
                
                missing_df = pd.DataFrame({
                    'Coluna': df.columns,
                    'Valores Ausentes': df.isnull().sum(),
                    '% Ausentes': (df.isnull().sum() / len(df) * 100).round(2)
                }).sort_values('% Ausentes', ascending=False)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(
                        missing_df[missing_df['Valores Ausentes'] > 0],
                        use_container_width=True
                    )
                
                with col2:
                    if len(missing_df[missing_df['Valores Ausentes'] > 0]) > 0:
                        fig = px.bar(
                            missing_df.head(20),
                            x='Coluna',
                            y='% Ausentes',
                            title='Top 20 Colunas com Valores Ausentes',
                            color='% Ausentes',
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Estatísticas
                st.write("### 📊 Estatísticas Descritivas")
                
                numeric_df = df.select_dtypes(include=[np.number])
                if not numeric_df.empty:
                    st.dataframe(numeric_df.describe(), use_container_width=True)
                else:
                    st.info("Não há colunas numéricas para análise estatística.")
            
            with tab3:
                # Visualizações
                st.subheader("Visualizações Interativas")
                
                # Seleção de tipo de gráfico
                chart_type = st.selectbox(
                    "Tipo de Gráfico:",
                    ["Histograma", "Barras", "Dispersão", "Box Plot"]
                )
                
                # Colunas disponíveis
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                
                if chart_type == "Histograma" and numeric_cols:
                    selected_col = st.selectbox("Selecione coluna:", numeric_cols)
                    if selected_col:
                        fig = px.histogram(
                            df,
                            x=selected_col,
                            nbins=30,
                            title=f"Distribuição de {selected_col}",
                            color_discrete_sequence=['#00A86B']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Barras" and categorical_cols:
                    selected_col = st.selectbox("Selecione coluna:", categorical_cols)
                    if selected_col:
                        top_n = st.slider("Número de categorias:", 5, 20, 10)
                        top_values = df[selected_col].value_counts().head(top_n)
                        
                        fig = px.bar(
                            x=top_values.index,
                            y=top_values.values,
                            title=f"Top {top_n} {selected_col}",
                            labels={'x': selected_col, 'y': 'Contagem'},
                            color=top_values.values,
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Dispersão" and len(numeric_cols) >= 2:
                    col_x = st.selectbox("Eixo X:", numeric_cols)
                    col_y = st.selectbox("Eixo Y:", numeric_cols)
                    
                    if col_x and col_y:
                        fig = px.scatter(
                            df,
                            x=col_x,
                            y=col_y,
                            title=f"{col_y} vs {col_x}",
                            trendline="ols",
                            opacity=0.6
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                # Exportação
                st.subheader("💾 Exportar Dados")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Exportar aba atual
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar aba atual (CSV)",
                        data=csv,
                        file_name=f"{selected_sheet.replace(' ', '_').replace('.', '_')}.csv",
                        mime="text/csv",
                        type="primary"
                    )
                
                with col2:
                    # Exportar todas as abas
                    if st.button("📚 Baixar todas as abas (ZIP)"):
                        import zipfile
                        from io import BytesIO
                        
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                            for sheet_name, sheet_df in st.session_state.dataframes.items():
                                csv_data = sheet_df.to_csv(index=False)
                                zip_file.writestr(
                                    f"{sheet_name.replace(' ', '_').replace('.', '_')}.csv",
                                    csv_data
                                )
                        
                        zip_buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_buffer,
                            file_name="fao_carbon_dataset_all_sheets.zip",
                            mime="application/zip"
                        )
                
                # Exportar análise
                st.write("### 📊 Exportar Análise")
                
                analysis_text = f"""
                # Análise da Aba: {selected_sheet}
                Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                
                ## Métricas:
                - Total de registros: {df.shape[0]}
                - Total de colunas: {df.shape[1]}
                - Colunas numéricas: {len(df.select_dtypes(include=[np.number]).columns)}
                - Dados preenchidos: {100 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100):.1f}%
                
                ## Colunas:
                {', '.join(df.columns.tolist()[:10])}...
                
                ## Estatísticas:
                {df.describe().to_string() if not df.select_dtypes(include=[np.number]).empty else 'Sem colunas numéricas'}
                """
                
                st.download_button(
                    label="📄 Baixar Relatório (TXT)",
                    data=analysis_text,
                    file_name=f"relatorio_{selected_sheet.replace(' ', '_')}.txt",
                    mime="text/plain"
                )
            
            # Footer
            st.markdown("---")
            st.caption(f"""
            📊 **FAO Agrifood Carbon Market Dashboard** • 
            Dados carregados de: [{GITHUB_USER}/{GITHUB_REPO}](https://github.com/{GITHUB_USER}/{GITHUB_REPO}) • 
            Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """)

if __name__ == "__main__":
    main()
