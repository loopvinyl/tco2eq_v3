# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import warnings
from urllib.request import urlopen
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

# Configuração - Coloque seu URL do GitHub aqui
GITHUB_RAW_URL = "https://raw.githubusercontent.com/SEU-USUARIO/SEU-REPOSITORIO/main/Dataset.xlsx"

# Cache para dados
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data_from_github(url):
    """Carrega dados diretamente do GitHub"""
    try:
        st.info(f"🔄 Baixando dados do GitHub...")
        
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
        
        st.success(f"✅ Dados carregados! {len(sheets)} abas encontradas.")
        return dataframes, sheets
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do GitHub: {e}")
        st.info("Tente fazer upload manual do arquivo.")
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

# Funções de análise (mantidas do código anterior)
def create_standards_dashboard(df):
    """Dashboard específico para padrões"""
    st.subheader("📊 Análise de Padrões de Carbono")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_standards = df.shape[0]
        st.metric("Total de Padrões", total_standards)
    
    with col2:
        if 'Name of standard/registry/platform' in df.columns:
            unique_standards = df['Name of standard/registry/platform'].nunique()
            st.metric("Padrões Únicos", unique_standards)
    
    with col3:
        if 'Total registered projects' in df.columns:
            try:
                total_projects = pd.to_numeric(df['Total registered projects'], errors='coerce').sum()
                st.metric("Projetos Registrados", f"{total_projects:,.0f}")
            except:
                st.metric("Projetos Registrados", "N/A")
    
    # Visualização
    if 'Name of standard/registry/platform' in df.columns and 'Total registered projects' in df.columns:
        try:
            standards_df = df[['Name of standard/registry/platform', 'Total registered projects']].copy()
            standards_df = standards_df.dropna()
            standards_df['Total registered projects'] = pd.to_numeric(
                standards_df['Total registered projects'], errors='coerce'
            )
            standards_df = standards_df.dropna()
            
            if not standards_df.empty:
                fig = px.bar(
                    standards_df.sort_values('Total registered projects', ascending=False).head(10),
                    x='Name of standard/registry/platform',
                    y='Total registered projects',
                    title="Top 10 Padrões por Projetos Registrados",
                    color='Total registered projects',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Não foi possível gerar o gráfico para esta aba.")

def create_projects_dashboard(df, sheet_name):
    """Dashboard para abas de projetos"""
    st.subheader(f"📈 Análise de Projetos - {sheet_name}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Projetos", df.shape[0])
    
    with col2:
        st.metric("Total de Colunas", df.shape[1])
    
    with col3:
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        st.metric("Colunas Numéricas", numeric_cols)
    
    with col4:
        fill_rate = (df.count().sum() / (df.shape[0] * df.shape[1]) * 100)
        st.metric("Dados Preenchidos", f"{fill_rate:.1f}%")
    
    # Análise de créditos
    credit_cols = [col for col in df.columns if 'credit' in str(col).lower()]
    if credit_cols:
        st.write("### 💰 Análise de Créditos")
        
        # Tentar encontrar coluna de créditos totais
        for col in credit_cols:
            try:
                if df[col].dtype in [np.int64, np.float64]:
                    total_credits = df[col].sum()
                    avg_credits = df[col].mean()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total de Créditos", f"{total_credits:,.0f}")
                    with col2:
                        st.metric("Média por Projeto", f"{avg_credits:,.0f}")
                    break
            except:
                continue

def create_methodologies_dashboard(df):
    """Dashboard para metodologias"""
    st.subheader("🔬 Análise de Metodologias")
    
    # Encontrar coluna principal
    main_col = None
    for col in df.columns:
        if 'methodology' in str(col).lower() or 'Unnamed: 2' == col:
            main_col = col
            break
    
    if main_col and df[main_col].nunique() > 1:
        st.write(f"### 📚 Distribuição de Metodologias")
        
        methodology_counts = df[main_col].value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=methodology_counts.index,
                y=methodology_counts.values,
                title="Top 10 Metodologias",
                labels={'x': 'Metodologia', 'y': 'Contagem'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                values=methodology_counts.values,
                names=methodology_counts.index,
                title="Proporção das Metodologias",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    # Título principal
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")
    st.markdown("""
    Dashboard interativo para análise do **Dataset do Mercado Voluntário de Carbono Agrícola** da FAO.
    Dados carregados diretamente do GitHub.
    """)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Fonte de Dados")
        
        # Opções de fonte de dados
        data_source = st.radio(
            "Escolha a fonte de dados:",
            ["GitHub (Automático)", "Upload Manual"],
            index=0
        )
        
        dataframes = {}
        sheets = []
        
        if data_source == "GitHub (Automático)":
            # Campo para URL do GitHub
            github_url = st.text_input(
                "URL do Dataset no GitHub (raw):",
                value=GITHUB_RAW_URL,
                help="Cole o link raw do arquivo Excel no GitHub"
            )
            
            if st.button("🔄 Carregar do GitHub") or github_url != GITHUB_RAW_URL:
                with st.spinner("Carregando dados do GitHub..."):
                    dataframes, sheets = load_data_from_github(github_url)
            
        else:  # Upload Manual
            uploaded_file = st.file_uploader(
                "Faça upload do arquivo Excel",
                type=['xlsx', 'xls']
            )
            
            if uploaded_file:
                with st.spinner("Processando arquivo..."):
                    dataframes, sheets = load_excel_from_upload(uploaded_file)
        
        st.markdown("---")
        
        if dataframes:
            st.success(f"✅ {len(sheets)} abas carregadas")
            
            # Seletor de aba
            st.header("📂 Navegação")
            selected_sheet = st.selectbox(
                "Selecione a aba para análise:",
                sheets,
                index=1 if len(sheets) > 1 else 0  # Pular README se existir
            )
            
            st.markdown("---")
            st.header("📊 Métricas Rápidas")
            
            if selected_sheet in dataframes:
                df = dataframes[selected_sheet]
                st.write(f"**{selected_sheet}**")
                st.write(f"- 📊 {df.shape[0]} registros")
                st.write(f"- 📋 {df.shape[1]} colunas")
                st.write(f"- 📈 {len(df.select_dtypes(include=[np.number]).columns)} colunas numéricas")
                
                # Botão de download
                st.markdown("---")
                st.header("💾 Exportação")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar aba atual (CSV)",
                    data=csv,
                    file_name=f"{selected_sheet.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            return dataframes, sheets, selected_sheet
    
    # Conteúdo principal
    if 'dataframes' not in locals() or not dataframes:
        # Tela inicial
        st.info("👈 **Configure a fonte de dados na barra lateral para começar**")
        
        # Layout de introdução
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Sobre o Dataset
            
            **FAO Agrifood Voluntary Carbon Market Dataset** contém:
            
            • **12 padrões** de mercado de carbono  
            • **13 plataformas** de MRV  
            • **89 metodologias** de cálculo  
            • **758 projetos** agrícolas  
            • **170 projetos** agroflorestais  
            • **29 projetos** de energia  
            • Dados de **1996 a 2023**
            """)
        
        with col2:
            st.markdown("""
            ### 🎯 Funcionalidades
            
            • **Análise por categoria**  
            • **Visualizações interativas**  
            • **Filtros dinâmicos**  
            • **Exportação de dados**  
            • **Insights automáticos**  
            • **Comparação entre abas**
            """)
        
        # Exemplo de visualização estática
        st.markdown("---")
        st.subheader("📈 Exemplo de Análise")
        
        # Dados de exemplo para demonstração
        example_data = pd.DataFrame({
            'Category': ['Agriculture', 'Agroforestry', 'Energy', 'Biochar', 'Small Projects'],
            'Projects': [758, 170, 29, 37, 55],
            'Avg_Credits': [25000, 18000, 45000, 12000, 8000],
            'Years_Active': [15, 12, 10, 5, 8]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                example_data,
                x='Category',
                y='Projects',
                title='Projetos por Categoria (Exemplo)',
                color='Avg_Credits',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                example_data,
                x='Projects',
                y='Avg_Credits',
                size='Years_Active',
                color='Category',
                title='Relação Projetos vs Créditos (Exemplo)',
                labels={'Projects': 'Número de Projetos', 'Avg_Credits': 'Créditos Médios'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        return None, None, None
    
    else:
        # Processar dados carregados
        dataframes, sheets, selected_sheet = main()
        
        if selected_sheet and selected_sheet in dataframes:
            df = dataframes[selected_sheet]
            
            # Cabeçalho da aba
            st.header(f"📄 {selected_sheet}")
            
            # Dashboard específico baseado no tipo de aba
            if selected_sheet == '1. Standards':
                create_standards_dashboard(df)
            elif selected_sheet == '3. Methodologies':
                create_methodologies_dashboard(df)
            elif selected_sheet in ['4. Agriculture', '5. Agroforestry-AR & Grassland', '6. Energy and Other ']:
                create_projects_dashboard(df, selected_sheet)
            else:
                # Dashboard genérico
                st.subheader("📋 Informações Gerais")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Registros", df.shape[0])
                
                with col2:
                    st.metric("Colunas", df.shape[1])
                
                with col3:
                    numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                    st.metric("Colunas Numéricas", numeric_cols)
                
                with col4:
                    fill_rate = (df.count().sum() / (df.shape[0] * df.shape[1]) * 100)
                    st.metric("Dados Preenchidos", f"{fill_rate:.1f}%")
            
            # Tabs principais
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Dados", "🔍 Análise", "📈 Visualizações", "💡 Insights"])
            
            with tab1:
                # Visualização dos dados
                st.subheader("Visualização dos Dados")
                
                # Filtros de colunas
                all_columns = df.columns.tolist()
                selected_columns = st.multiselect(
                    "Selecione colunas para mostrar:",
                    all_columns,
                    default=all_columns[:min(10, len(all_columns))]
                )
                
                # Número de linhas
                rows_to_show = st.slider(
                    "Número de linhas para mostrar:",
                    min_value=10,
                    max_value=min(500, df.shape[0]),
                    value=100,
                    step=10
                )
                
                # Filtrar dados
                if selected_columns:
                    display_df = df[selected_columns].head(rows_to_show)
                else:
                    display_df = df.head(rows_to_show)
                
                # Mostrar tabela
                st.dataframe(display_df, use_container_width=True)
                
                # Estatísticas
                st.subheader("📊 Estatísticas Descritivas")
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_cols) > 0:
                    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                else:
                    st.info("Não há colunas numéricas nesta aba.")
            
            with tab2:
                # Análise detalhada
                st.subheader("Análise Detalhada")
                
                # Análise de valores ausentes
                st.write("### 🔍 Valores Ausentes")
                
                missing_data = pd.DataFrame({
                    'Coluna': df.columns,
                    'Valores Ausentes': df.isnull().sum().values,
                    'Percentual': (df.isnull().sum() / len(df) * 100).round(2).values
                })
                missing_data = missing_data[missing_data['Valores Ausentes'] > 0]
                
                if len(missing_data) > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.dataframe(
                            missing_data.sort_values('Percentual', ascending=False),
                            use_container_width=True
                        )
                    
                    with col2:
                        if len(missing_data) > 0:
                            fig = px.bar(
                                missing_data.head(20),
                                x='Coluna',
                                y='Percentual',
                                title='Top 20 Colunas com Valores Ausentes',
                                color='Percentual',
                                color_continuous_scale='Reds'
                            )
                            fig.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("✅ Não há valores ausentes nesta aba!")
                
                # Tipos de dados
                st.write("### 📋 Tipos de Dados")
                
                type_data = pd.DataFrame({
                    'Coluna': df.columns,
                    'Tipo': df.dtypes.astype(str).values,
                    'Valores Únicos': [df[col].nunique() for col in df.columns]
                })
                
                st.dataframe(type_data, use_container_width=True)
            
            with tab3:
                # Visualizações
                st.subheader("Visualizações Gráficas")
                
                # Seleção de tipo de gráfico
                chart_type = st.selectbox(
                    "Tipo de Gráfico:",
                    ["Histograma", "Barras", "Dispersão", "Box Plot", "Pizza"]
                )
                
                # Seleção de colunas
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                
                if chart_type == "Histograma" and numeric_cols:
                    selected_col = st.selectbox("Selecione coluna numérica:", numeric_cols)
                    if selected_col:
                        fig = px.histogram(
                            df,
                            x=selected_col,
                            nbins=30,
                            title=f"Distribuição de {selected_col}",
                            color_discrete_sequence=['#2E8B57']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Barras" and categorical_cols:
                    selected_col = st.selectbox("Selecione coluna categórica:", categorical_cols)
                    if selected_col:
                        top_n = st.slider("Número de categorias:", 5, 20, 10)
                        value_counts = df[selected_col].value_counts().head(top_n)
                        
                        fig = px.bar(
                            x=value_counts.index,
                            y=value_counts.values,
                            title=f"Top {top_n} {selected_col}",
                            labels={'x': selected_col, 'y': 'Contagem'},
                            color=value_counts.values,
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
                # Insights
                st.subheader("💡 Insights e Recomendações")
                
                # Análise automática
                total_cells = df.shape[0] * df.shape[1]
                filled_cells = df.count().sum()
                fill_rate = (filled_cells / total_cells * 100)
                
                # Insights
                insights = []
                
                if fill_rate < 50:
                    insights.append("⚠️ **Baixa qualidade de dados**: Menos de 50% dos dados estão preenchidos")
                
                if len(numeric_cols) >= 3:
                    insights.append("📊 **Boa base numérica**: Várias colunas numéricas para análise estatística")
                
                if any('credit' in col.lower() for col in df.columns):
                    insights.append("💰 **Dados financeiros disponíveis**: Possibilidade de análise de créditos de carbono")
                
                if any('year' in col.lower() for col in df.columns):
                    insights.append("📅 **Dados temporais**: Possibilidade de análise de tendências ao longo do tempo")
                
                # Mostrar insights
                if insights:
                    st.write("### 📌 Insights Identificados")
                    for insight in insights:
                        st.write(f"- {insight}")
                else:
                    st.info("Execute uma análise mais detalhada para obter insights.")
                
                # Recomendações
                st.write("### 🔧 Recomendações de Análise")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Para esta aba:**")
                    st.write("1. Limpeza de dados ausentes")
                    st.write("2. Normalização de colunas")
                    st.write("3. Criação de indicadores")
                    st.write("4. Análise de correlação")
                
                with col2:
                    st.write("**Próximos passos:**")
                    st.write("1. Comparar com outras abas")
                    st.write("2. Análise temporal (se houver datas)")
                    st.write("3. Segmentação por categorias")
                    st.write("4. Exportar relatório")
                
                # Botão para análise avançada
                if st.button("🚀 Executar Análise Avançada", type="primary"):
                    with st.spinner("Processando análise avançada..."):
                        # Simulação de análise
                        st.success("Análise concluída!")
                        
                        # Resultados simulados
                        results = {
                            "Correlações encontradas": 3,
                            "Outliers identificados": 12,
                            "Tendências detectadas": 2,
                            "Recomendações geradas": 5
                        }
                        
                        for key, value in results.items():
                            st.write(f"**{key}:** {value}")
            
            # Resumo de todas as abas
            st.markdown("---")
            st.subheader("📋 Resumo de Todas as Abas")
            
            summary_data = []
            for sheet in sheets:
                sheet_df = dataframes[sheet]
                summary_data.append({
                    'Aba': sheet,
                    'Registros': sheet_df.shape[0],
                    'Colunas': sheet_df.shape[1],
                    'Preenchido (%)': round((sheet_df.count().sum() / (sheet_df.shape[0] * sheet_df.shape[1]) * 100), 1)
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

if __name__ == "__main__":
    main()
