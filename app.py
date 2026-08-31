import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da Página
st.set_page_config(
    page_title="Plano de Desmobilização - Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-card-danger {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0F172A;
    }
    </style>
""", unsafe_allow_html=True)

DEFAULT_PATH = "Estudo_primarizacao_desmob.xlsx"

@st.cache_data(ttl=60)
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df_equipes = pd.read_excel(file_path, sheet_name="Base - Equipes Placas")
        df_equipes.columns = [str(c).strip() for c in df_equipes.columns]
        return df_equipes
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

# Sidebar para Filtros e Caminho
st.sidebar.title("📌 Configurações & Filtros")
path_input = st.sidebar.text_input("Caminho do Arquivo Excel", value=DEFAULT_PATH)

df_equipes = load_data(path_input)

if df_equipes is None:
    st.warning(f"⚠️ Não foi possível carregar o arquivo no caminho: `{path_input}`.")
    st.info("Por favor, verifique se o arquivo `Estudo_primarizacao_desmob.xlsx` existe na pasta informada.")
    st.stop()

# Identificação das Colunas
col_placa = "PLACA" if "PLACA" in df_equipes.columns else df_equipes.columns[8]
col_status_viatura = "Status Viatura" if "Status Viatura" in df_equipes.columns else df_equipes.columns[10]
col_desmob = "DESMOBIZAÇÃO" if "DESMOBIZAÇÃO" in df_equipes.columns else df_equipes.columns[7]

# Sidebar - Filtros Interativos
st.sidebar.subheader("Filtros da Base de Equipes")

opcoes_polo = sorted([str(x) for x in df_equipes["Polo"].dropna().unique()]) if "Polo" in df_equipes.columns else []
opcoes_super = sorted([str(x) for x in df_equipes["Supervisor"].dropna().unique()]) if "Supervisor" in df_equipes.columns else []
opcoes_status = sorted([str(x) for x in df_equipes[col_status_viatura].dropna().unique()])

polos = st.sidebar.multiselect("Polo", options=opcoes_polo)
supervisores = st.sidebar.multiselect("Supervisor", options=opcoes_super)
status_viatura = st.sidebar.multiselect("Status Viatura", options=opcoes_status)

# Aplicação dos Filtros
df_filtered = df_equipes.copy()

if polos and "Polo" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Polo"].astype(str).isin(polos)]

if supervisores and "Supervisor" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Supervisor"].astype(str).isin(supervisores)]

if status_viatura:
    df_filtered = df_filtered[df_filtered[col_status_viatura].astype(str).isin(status_viatura)]

# Regra da Frota/Viaturas:
# 1. Ignorar placas "SEM PLACA", vazias, NAN ou NONE
placa_limpa = df_filtered[col_placa].astype(str).str.strip().str.upper()
mask_placa_valida = ~placa_limpa.isin(['SEM PLACA', 'NAN', 'NONE', '']) & df_filtered[col_placa].notna()

df_valid_placas = df_filtered[mask_placa_valida].copy()

# 2. Considerar desmobilização se Status Viatura contiver 'DEVOLVER VIATURA'
status_viatura_clean = df_valid_placas[col_status_viatura].astype(str).str.strip().str.upper()
mask_devolver = status_viatura_clean.str.contains('DEVOLVER VIATURA', na=False)

# Título Principal
st.markdown("<div class='main-header'>📊 PAINEL DE DESMOBILIZAÇÃO & GESTÃO DE FROTA</div>", unsafe_allow_html=True)

# Tabs Principais
tab_resumo, tab_frota = st.tabs([
    "📉 Cronograma & Indicadores Globais", 
    "🚗 Frota & Veículos (Visão Geral)"
])

with tab_resumo:
    st.subheader("📌 Indicadores Globais do Plano")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-card'><div class='metric-title'>Equipes Atuais</div><div class='metric-value'>87</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card-danger'><div class='metric-title'>Saídas Previstas</div><div class='metric-value' style='color:#DC2626;'>31</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card'><div class='metric-title'>Equipes Finais</div><div class='metric-value' style='color:#16A34A;'>56</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Cronograma Solicitado
    st.subheader("📅 Cronograma de Desmobilização & Redução Financeira (Linha do Tempo)")
    
    df_cronograma = pd.DataFrame({
        "Mês": ["jul/26", "ago/26", "set/26", "out/26", "nov/26", "dez/26"],
        "Contrato sem reequilíbrio (R$)": [5201230.46, 5000419.15, 4700201.12, 4124117.26, 3322869.89, 3022651.85],
        "Equipes que saem": [1, 3, 4, 8, 11, 4],
        "Acumulado Saídas": [1, 4, 8, 16, 27, 31]
    })

    fig_timeline = go.Figure()

    fig_timeline.add_trace(go.Bar(
        x=df_cronograma["Mês"],
        y=df_cronograma["Contrato sem reequilíbrio (R$)"],
        name='Contrato sem reequilíbrio (R$)',
        marker_color='#2563EB',
        text=[f"R$ {val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") for val in df_cronograma["Contrato sem reequilíbrio (R$)"]],
        textposition='outside'
    ))

    fig_timeline.add_trace(go.Scatter(
        x=df_cronograma["Mês"],
        y=df_cronograma["Acumulado Saídas"],
        mode='lines+markers+text',
        name='Desmobilizados Acumulado',
        text=df_cronograma["Acumulado Saídas"],
        textposition="top center",
        yaxis='y2',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=8)
    ))

    fig_timeline.update_layout(
        title="Valor do Contrato Sem Reequilíbrio vs Evolução das Saídas",
        xaxis_title="Mês",
        yaxis=dict(title="Contrato sem reequilíbrio (R$)", showgrid=True),
        yaxis2=dict(title="Saídas Acumuladas (Equipes)", overlaying='y', side='right', showgrid=False, range=[0, 35]),
        hovermode="x unified",
        template="plotly_white",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_timeline, use_container_width=True)

    with st.expander("📋 Ver Tabela Detalhada do Cronograma", expanded=False):
        df_cron_view = df_cronograma.copy()
        df_cron_view["Contrato sem reequilíbrio (R$)"] = df_cron_view["Contrato sem reequilíbrio (R$)"].map(lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
        st.dataframe(df_cron_view, use_container_width=True)

    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        st.subheader("💰 Cenário Financeiro 2026")
        fig_fin = go.Figure(data=[
            go.Bar(name='Atual', x=['Valor 2026'], y=[5276284.97], marker_color='#1E40AF', text=['R$ 5.276.284,97'], textposition='auto'),
            go.Bar(name='Pós-Desmobilização', x=['Valor 2026'], y=[3944192.76], marker_color='#16A34A', text=['R$ 3.944.192,76'], textposition='auto')
        ])
        fig_fin.update_layout(barmode='group', template='plotly_white', height=350)
        st.plotly_chart(fig_fin, use_container_width=True)

    with col_fin2:
        st.subheader("📊 Reequilíbrio por Tipo de Equipe")
        df_reeq = pd.DataFrame({
            "Tipo": ["Moto Corte", "Comercial", "Emergência", "Grupo A"],
            "Percentual": [81, 21, 29, 28]
        })
        fig_reeq = px.bar(df_reeq, x="Tipo", y="Percentual", text="Percentual", color="Tipo", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_reeq.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_reeq.update_layout(showlegend=False, template='plotly_white', height=350, yaxis_range=[0, 100])
        st.plotly_chart(fig_reeq, use_container_width=True)

with tab_frota:
    st.subheader("🚗 Visão Geral da Frota & Indicadores de Desmobilização")
    
    # Cálculo das métricas de viatura (Placas Únicas)
    df_desmob_viaturas = df_valid_placas[mask_devolver]
    
    placas_totais_unicas = df_valid_placas[col_placa].nunique()
    placas_desmob_unicas = df_desmob_viaturas[col_placa].nunique()
    placas_manter_unicas = placas_totais_unicas - placas_desmob_unicas

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registros Exibidos", len(df_filtered))
    m2.metric("Placas a Manter", placas_manter_unicas)
    m3.metric("Viaturas a Desmobilizar (Placas Únicas)", placas_desmob_unicas, delta=f"-{placas_desmob_unicas}", delta_color="inverse")
    m4.metric("Total de Placas Únicas", placas_totais_unicas)

    st.markdown("---")

    # Linha do Tempo de Desmobilização na Frota
    st.markdown("### 📈 Linha do Tempo: Saída Acumulada de Veículos")
    
    df_desmob_timeline = pd.DataFrame({
        "Mês": ["jul/26", "ago/26", "set/26", "out/26", "nov/26", "dez/26"],
        "Saídas Mensais": [1, 3, 4, 8, 11, 4],
        "Desmobilizados Acumulado": [1, 4, 8, 16, 27, 31]
    })

    fig_desmob_line = px.line(
        df_desmob_timeline, 
        x="Mês", 
        y="Desmobilizados Acumulado", 
        markers=True, 
        text="Desmobilizados Acumulado",
        title="Curva de Crescimento das Desmobilizações (Jul/26 - Dez/26)",
        color_discrete_sequence=["#EF4444"]
    )
    fig_desmob_line.update_traces(textposition="top left", line=dict(width=3))
    fig_desmob_line.update_layout(template="plotly_white", height=350, yaxis_range=[0, 35])
    st.plotly_chart(fig_desmob_line, use_container_width=True)

    # Gráfico de Distribuição por Polo (Contagem de Viaturas Únicas a Desmobilizar)
    st.markdown("### 📊 Viaturas a Desmobilizar por Polo (Placas Únicas)")
    
    if "Polo" in df_desmob_viaturas.columns and not df_desmob_viaturas.empty:
        df_polo = df_desmob_viaturas.groupby("Polo")[col_placa].nunique().reset_index()
        df_polo.columns = ["Polo", "Viaturas a Devolver"]
        fig_polo = px.bar(
            df_polo, 
            x="Polo", 
            y="Viaturas a Devolver", 
            color="Polo", 
            text="Viaturas a Devolver", 
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_polo.update_layout(showlegend=False, height=350, template="plotly_white")
        st.plotly_chart(fig_polo, use_container_width=True)
    else:
        st.info("Nenhuma viatura para devolver nos filtros selecionados.")

    st.markdown("---")
    st.markdown("### 📋 Tabela Geral de Viaturas (Filtrada)")

    def highlight_rows(row):
        stat = str(row.get(col_status_viatura, '')).strip().upper()
        placa = str(row.get(col_placa, '')).strip().upper()
        if 'DEVOLVER VIATURA' in stat and placa not in ['SEM PLACA', 'NAN', 'NONE', '']:
            return ['background-color: #FEE2E2; color: #991B1B; font-weight: bold;'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_filtered.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=400
    )
