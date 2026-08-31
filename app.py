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
        return None, None
    try:
        df_painel = pd.read_excel(file_path, sheet_name="Painel")
        df_equipes = pd.read_excel(file_path, sheet_name="Base - Equipes Placas")
        
        # Limpeza de nomes de colunas
        df_equipes.columns = [str(c).strip() for c in df_equipes.columns]
        
        return df_painel, df_equipes
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None, None

# Sidebar para Filtros e Caminho
st.sidebar.title("📌 Configurações & Filtros")
path_input = st.sidebar.text_input("Caminho do Arquivo Excel", value=DEFAULT_PATH)

df_painel, df_equipes = load_data(path_input)

if df_equipes is None:
    st.warning(f"⚠️ Não foi possível carregar o arquivo no caminho: `{path_input}`.")
    st.info("Por favor, verifique se o arquivo `Estudo_primarizacao_desmob.xlsx` existe na pasta informada.")
    st.stop()

# Colunas Essenciais
col_placa = "PLACA" if "PLACA" in df_equipes.columns else df_equipes.columns[8]
col_status_viatura = "Status Viatura" if "Status Viatura" in df_equipes.columns else df_equipes.columns[10]
col_desmob = "DESMOBIZAÇÃO" if "DESMOBIZAÇÃO" in df_equipes.columns else df_equipes.columns[7]

# Sidebar - Filtros Interativos
st.sidebar.subheader("Filtros da Base de Equipes")

opcoes_polo = sorted([str(x) for x in df_equipes["Polo"].dropna().unique()]) if "Polo" in df_equipes.columns else []
opcoes_super = sorted([str(x) for x in df_equipes["Supervisor"].dropna().unique()]) if "Supervisor" in df_equipes.columns else []
opcoes_desmob = sorted([str(x) for x in df_equipes[col_desmob].dropna().unique()])
opcoes_status = sorted([str(x) for x in df_equipes[col_status_viatura].dropna().unique()])

polos = st.sidebar.multiselect("Polo", options=opcoes_polo)
supervisores = st.sidebar.multiselect("Supervisor", options=opcoes_super)
status_desmob = st.sidebar.multiselect("Desmobilização", options=opcoes_desmob)
status_viatura = st.sidebar.multiselect("Status Viatura", options=opcoes_status)

# Toggle para desduplicar veículos compartilhados
desduplicar_placas = st.sidebar.checkbox("🚗 Filtrar Veículos Únicos (Remover Placas Duplicadas)", value=False)

# Aplicação dos Filtros na Base
df_filtered = df_equipes.copy()

if polos and "Polo" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Polo"].astype(str).isin(polos)]

if supervisores and "Supervisor" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Supervisor"].astype(str).isin(supervisores)]

if status_desmob:
    df_filtered = df_filtered[df_filtered[col_desmob].astype(str).isin(status_desmob)]

if status_viatura:
    df_filtered = df_filtered[df_filtered[col_status_viatura].astype(str).isin(status_viatura)]

# Tratativa para remoção de veículos duplicados (Carros Compartilhados)
if desduplicar_placas:
    placas_validas = df_filtered[~df_filtered[col_placa].astype(str).str.upper().isin(['SEM PLACA', 'NAN', 'NONE', ''])]
    placas_sem_id = df_filtered[df_filtered[col_placa].astype(str).str.upper().isin(['SEM PLACA', 'NAN', 'NONE', ''])]
    
    placas_unicas = placas_validas.drop_duplicates(subset=[col_placa], keep='first')
    df_filtered = pd.concat([placas_unicas, placas_sem_id], ignore_index=True)

# Lógica atualizada de Desmobilização: considera desmobilizada qualquer viatura que NÃO seja "NÃO"
col_desmob_str = df_filtered[col_desmob].astype(str).str.strip().str.upper()
mask_desmob = ~col_desmob_str.isin(['NÃO', 'NAO', 'NAN', '', 'NONE']) & df_filtered[col_desmob].notna()

# Título Principal
st.markdown("<div class='main-header'>📊 PAINEL DE DESMOBILIZAÇÃO & GESTÃO DE FROTA</div>", unsafe_allow_html=True)

# Tabs Principais
tab_resumo, tab_frota, tab_desmob_lista, tab_painel_raw = st.tabs([
    "📉 Cronograma & Indicadores Global", 
    "🚗 Frota & Veículos (Visão Geral)", 
    "🚨 Veículos a Desmobilizar (Lista Dedicada)", 
    "📑 Dados Brutos (Painel)"
])

with tab_resumo:
    st.subheader("📌 Indicadores Globais do Plano")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card'><div class='metric-title'>Equipes Atuais</div><div class='metric-value'>87</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card-danger'><div class='metric-title'>Saídas Previstas</div><div class='metric-value' style='color:#DC2626;'>31</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card'><div class='metric-title'>Equipes Finais</div><div class='metric-value' style='color:#16A34A;'>56</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card'><div class='metric-title'>Viaturas Mapeadas</div><div class='metric-value'>70</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Cronograma Solicitado
    st.subheader("📅 Cronograma de Desmobilização & Redução Financeira (Linha do Tempo)")
    
    df_cronograma = pd.DataFrame({
        "Mês": ["jul/26", "ago/26", "set/26", "out/26", "nov/26", "dez/26"],
        "Equipes que saem": [1, 3, 4, 8, 11, 4],
        "Acumulado": [1, 4, 8, 16, 27, 31],
        "Equipes restantes": [87, 84, 80, 72, 61, 57],
        "Redução sem reequilíbrio (R$)": [75054.51, 200811.31, 300218.03, 576083.85, 801247.38, 300218.03]
    })

    fig_timeline = go.Figure()

    fig_timeline.add_trace(go.Scatter(
        x=df_cronograma["Mês"],
        y=df_cronograma["Equipes restantes"],
        mode='lines+markers+text',
        name='Equipes Restantes',
        text=df_cronograma["Equipes restantes"],
        textposition="top center",
        line=dict(color='#2563EB', width=3),
        marker=dict(size=8)
    ))

    fig_timeline.add_trace(go.Bar(
        x=df_cronograma["Mês"],
        y=df_cronograma["Redução sem reequilíbrio (R$)"],
        name='Redução sem Reequilíbrio (R$)',
        marker_color='rgba(239, 68, 68, 0.4)',
        yaxis='y2',
        text=[f"R$ {val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") for val in df_cronograma["Redução sem reequilíbrio (R$)"]],
        textposition='outside'
    ))

    fig_timeline.add_trace(go.Scatter(
        x=df_cronograma["Mês"],
        y=[56] * len(df_cronograma),
        mode='lines',
        name='Meta Pós-Desmobilização (56 Equipes)',
        line=dict(color='#16A34A', width=2, dash='dash')
    ))

    fig_timeline.update_layout(
        title="Linha do Tempo: Saída de Equipes vs Redução de Custo Acumulada",
        xaxis_title="Mês",
        yaxis=dict(title="Quantidade de Equipes", range=[40, 95]),
        yaxis2=dict(title="Redução sem Reequilíbrio (R$)", overlaying='y', side='right', showgrid=False),
        hovermode="x unified",
        template="plotly_white",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_timeline, use_container_width=True)

    with st.expander("📋 Ver Tabela Detalhada do Cronograma", expanded=False):
        df_cron_view = df_cronograma.copy()
        df_cron_view["Redução sem reequilíbrio (R$)"] = df_cron_view["Redução sem reequilíbrio (R$)"].map(lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
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
    
    total_linhas = len(df_filtered)
    devolver = len(df_filtered[mask_desmob])
    manter = total_linhas - devolver

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registros Exibidos", total_linhas)
    m2.metric("Veículos a Manter", manter)
    m3.metric("Veículos a Desmobilizar", devolver, delta=f"-{devolver}", delta_color="inverse")
    
    placas_unicas_count = df_filtered[col_placa].nunique()
    m4.metric("Placas Distintas", placas_unicas_count)

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

    # Gráficos Operacionais
    st.markdown("### 📊 Visibilidade da Frota por Filtro Selecionado")
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        st.markdown("##### 📌 Veículos por Status de Desmobilização")
        df_desmob_cnt = df_filtered[col_desmob].value_counts().reset_index()
        df_desmob_cnt.columns = ["Status", "Quantidade"]
        fig_desmob_pie = px.pie(df_desmob_cnt, names="Status", values="Quantidade", hole=0.4, color_discrete_sequence=["#EF4444", "#10B981", "#F59E0B"])
        fig_desmob_pie.update_layout(height=300)
        st.plotly_chart(fig_desmob_pie, use_container_width=True)
            
    with col_g2:
        st.markdown("##### 📌 Distribuição por Polo")
        if "Polo" in df_filtered.columns:
            df_polo = df_filtered["Polo"].value_counts().reset_index()
            df_polo.columns = ["Polo", "Quantidade"]
            fig_polo = px.bar(df_polo, x="Polo", y="Quantidade", color="Polo", text="Quantidade", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_polo.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_polo, use_container_width=True)

    with col_g3:
        st.markdown("##### 📌 Frota por Supervisor")
        if "Supervisor" in df_filtered.columns:
            df_super = df_filtered["Supervisor"].value_counts().reset_index()
            df_super.columns = ["Supervisor", "Quantidade"]
            fig_super = px.bar(df_super, x="Supervisor", y="Quantidade", color="Supervisor", text="Quantidade", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_super.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_super, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Tabela Geral de Viaturas (Filtrada)")

    def highlight_rows(row):
        desm = str(row.get(col_desmob, '')).strip().upper()
        if desm not in ['NÃO', 'NAO', 'NAN', '', 'NONE']:
            return ['background-color: #FEE2E2; color: #991B1B; font-weight: bold;'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_filtered.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=400
    )

with tab_desmob_lista:
    st.subheader("🚨 Lista Dedicada de Veículos a Desmobilizar")
    st.info("Esta aba exibe **apenas** as viaturas/equipes com data programada para desmobilização (`DESMOBIZAÇÃO ≠ NÃO`).")
    
    # Filtrando apenas os veículos marcados para desmobilizar
    df_desmob_only = df_filtered[mask_desmob].copy()

    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("Total a Desmobilizar (Filtro Atual)", len(df_desmob_only))
    col_d2.metric("Placas Únicas a Devolver", df_desmob_only[col_placa].nunique() if col_placa in df_desmob_only.columns else 0)
    
    if "Polo" in df_desmob_only.columns and not df_desmob_only.empty:
        polo_top = df_desmob_only["Polo"].mode()[0] if not df_desmob_only["Polo"].empty else "N/A"
        col_d3.metric("Polo com Mais Saídas", polo_top)

    st.markdown("---")

    # Gráficos da aba exclusiva de desmobilização
    col_dm1, col_dm2 = st.columns(2)
    with col_dm1:
        st.markdown("##### 📊 Desmobilizações por Polo")
        if "Polo" in df_desmob_only.columns and not df_desmob_only.empty:
            df_polo_d = df_desmob_only["Polo"].value_counts().reset_index()
            df_polo_d.columns = ["Polo", "Quantidade"]
            fig_polo_d = px.bar(df_polo_d, x="Polo", y="Quantidade", text="Quantidade", color_discrete_sequence=["#DC2626"])
            fig_polo_d.update_layout(height=300, template="plotly_white")
            st.plotly_chart(fig_polo_d, use_container_width=True)
        else:
            st.write("Nenhum registro para exibir.")

    with col_dm2:
        st.markdown("##### 📊 Desmobilizações por Supervisor")
        if "Supervisor" in df_desmob_only.columns and not df_desmob_only.empty:
            df_super_d = df_desmob_only["Supervisor"].value_counts().reset_index()
            df_super_d.columns = ["Supervisor", "Quantidade"]
            fig_super_d = px.bar(df_super_d, x="Supervisor", y="Quantidade", text="Quantidade", color_discrete_sequence=["#B91C1C"])
            fig_super_d.update_layout(height=300, template="plotly_white")
            st.plotly_chart(fig_super_d, use_container_width=True)
        else:
            st.write("Nenhum registro para exibir.")

    st.markdown("### 📋 Tabela Exclusiva: Viaturas Marcadas para Desmobilização")
    st.dataframe(
        df_desmob_only.style.set_properties(**{'background-color': '#FEF2F2', 'color': '#991B1B', 'font-weight': 'bold'}),
        use_container_width=True,
        height=400
    )

    # Download apenas dos desmobilizados
    csv_desmob = df_desmob_only.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Apenas Lista de Desmobilizados (CSV)",
        data=csv_desmob,
        file_name='veiculos_desmobilizar_filtrados.csv',
        mime='text/csv',
    )

with tab_painel_raw:
    st.subheader("📑 Visualização dos Dados Brutos da Aba Painel")
    if df_painel is not None:
        st.dataframe(df_painel, use_container_width=True)
    else:
        st.info("Aba Painel não carregada.")
