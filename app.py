import streamlit as st
import pandas as pd
from database import Database

# Configuração da página
st.set_page_config(
    page_title="Sistema Eleitoral",
    page_icon="🗳️",
    layout="wide"
)

# Inicializar banco de dados
db = Database()

def main():
    st.title("🗳️ Sistema Eleitoral")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["Início", "Cadastrar Candidato", "Gerenciar Candidatos", "Cadastrar Eleitor", "Votação", "Resultados"]
    )
    
    if menu == "Início":
        mostrar_inicio()
    elif menu == "Cadastrar Candidato":
        cadastrar_candidato()
    elif menu == "Gerenciar Candidatos":
        gerenciar_candidatos()
    elif menu == "Cadastrar Eleitor":
        cadastrar_eleitor()
    elif menu == "Votação":
        votacao()
    elif menu == "Resultados":
        mostrar_resultados()

def mostrar_inicio():
    st.header("Bem-vindo ao Sistema Eleitoral")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Eleitores", db.total_eleitores())
    
    with col2:
        st.metric("Total de Votos", db.total_votos())
    
    with col3:
        candidatos_ativos = len(db.listar_candidatos(ativo=True))
        st.metric("Candidatos Ativos", candidatos_ativos)
    
    st.subheader("Estatísticas Rápidas")
    resultados = db.obter_resultados()
    if resultados:
        df = pd.DataFrame(resultados, columns=['Cargo', 'Nome', 'Partido', 'Número', 'Votos'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum candidato cadastrado ainda.")

def cadastrar_candidato():
    st.header("Cadastrar Novo Candidato")
    
    with st.form("form_candidato"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo")
            partido = st.text_input("Partido")
        
        with col2:
            numero = st.number_input("Número", min_value=10, max_value=999, step=1)
            cargo = st.selectbox("Cargo", ["Prefeito", "Vereador", "Governador", "Deputado", "Presidente"])
        
        submitted = st.form_submit_button("Cadastrar Candidato")
        
        if submitted:
            if nome and partido and numero and cargo:
                if db.criar_candidato(nome, partido, numero, cargo):
                    st.success("Candidato cadastrado com sucesso!")
                else:
                    st.error("Erro ao cadastrar candidato. Número já existe.")
            else:
                st.warning("Por favor, preencha todos os campos.")

def gerenciar_candidatos():
    st.header("Gerenciar Candidatos")
    
    candidatos = db.listar_candidatos(ativo=True)
    
    if not candidatos:
        st.info("Nenhum candidato cadastrado.")
        return
    
    for candidato in candidatos:
        id_candidato, nome, partido, numero, cargo, votos, ativo, data_cadastro = candidato
        
        with st.expander(f"{cargo} - {nome} ({partido}) - Nº {numero}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Votos recebidos:** {votos}")
                st.write(f"**Cadastrado em:** {data_cadastro}")
            
            with col2:
                if st.button("Excluir", key=f"del_{id_candidato}"):
                    if db.excluir_candidato(id_candidato):
                        st.success("Candidato excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir candidato.")

def cadastrar_eleitor():
    st.header("Cadastrar Eleitor")
    
    with st.form("form_eleitor"):
        cpf = st.text_input("CPF (apenas números)", max_chars=11)
        nome = st.text_input("Nome Completo")
        email = st.text_input("Email (opcional)")
        
        submitted = st.form_submit_button("Cadastrar Eleitor")
        
        if submitted:
            if cpf and nome:
                if len(cpf) == 11 and cpf.isdigit():
                    if db.criar_usuario(cpf, nome, email):
                        st.success("Eleitor cadastrado com sucesso!")
                    else:
                        st.error("CPF já cadastrado.")
                else:
                    st.error("CPF deve conter exatamente 11 números.")
            else:
                st.warning("Por favor, preencha pelo menos CPF e Nome.")

def votacao():
    st.header("Sistema de Votação")
    
    # Verificação do eleitor
    cpf = st.text_input("Digite seu CPF para votar", key="cpf_votacao")
    
    if cpf:
        if len(cpf) == 11 and cpf.isdigit():
            ja_votou = db.verificar_usuario_ja_votou(cpf)
            
            if ja_votou is None:
                st.error("CPF não cadastrado. Por favor, cadastre-se primeiro.")
                return
            elif ja_votou:
                st.error("Você já votou! Cada eleitor pode votar apenas uma vez.")
                return
            else:
                st.success("CPF verificado! Você pode votar.")
                
                # Lista de candidatos por cargo
                candidatos = db.listar_candidatos(ativo=True)
                
                if not candidatos:
                    st.error("Nenhum candidato disponível para votação.")
                    return
                
                # Agrupar candidatos por cargo
                cargos = {}
                for candidato in candidatos:
                    id_candidato, nome, partido, numero, cargo, votos, ativo, data_cadastro = candidato
                    if cargo not in cargos:
                        cargos[cargo] = []
                    cargos[cargo].append(candidato)
                
                # Interface de votação
                votos = {}
                
                for cargo, candidatos_cargo in cargos.items():
                    st.subheader(f"Votação para {cargo}")
                    
                    opcoes = [f"Nº {c[3]} - {c[1]} ({c[2]})" for c in candidatos_cargo]
                    opcoes.insert(0, "Voto em Branco")
                    
                    voto = st.radio(
                        f"Selecione seu candidato para {cargo}:",
                        opcoes,
                        key=f"voto_{cargo}"
                    )
                    
                    if voto != "Voto em Branco":
                        # Extrair ID do candidato selecionado
                        numero_selecionado = int(voto.split(" - ")[0].replace("Nº ", ""))
                        candidato_selecionado = next(c for c in candidatos_cargo if c[3] == numero_selecionado)
                        votos[cargo] = candidato_selecionado[0]  # ID do candidato
                
                # Botão para confirmar votação
                if st.button("Confirmar Votos"):
                    # Registrar votos para cada cargo
                    sucesso = True
                    for cargo, candidato_id in votos.items():
                        if not db.registrar_voto(cpf, candidato_id):
                            sucesso = False
                    
                    if sucesso:
                        st.success("Voto registrado com sucesso! Obrigado por participar.")
                    else:
                        st.error("Erro ao registrar voto. Por favor, tente novamente.")
        else:
            st.error("Por favor, digite um CPF válido com 11 números.")

def mostrar_resultados():
    st.header("Resultados da Eleição")
    
    resultados = db.obter_resultados()
    
    if not resultados:
        st.info("Nenhum voto registrado ainda.")
        return
    
    # Agrupar resultados por cargo
    cargos = {}
    for resultado in resultados:
        cargo = resultado[0]
        if cargo not in cargos:
            cargos[cargo] = []
        cargos[cargo].append(resultado[1:])  # Remove o cargo da tupla
    
    for cargo, candidatos in cargos.items():
        st.subheader(f"Resultados para {cargo}")
        
        # Ordenar por votos (decrescente)
        candidatos.sort(key=lambda x: x[3], reverse=True)
        
        # Criar DataFrame para exibição
        df = pd.DataFrame(candidatos, columns=['Nome', 'Partido', 'Número', 'Votos'])
        df['Posição'] = range(1, len(df) + 1)
        
        # Reordenar colunas
        df = df[['Posição', 'Nome', 'Partido', 'Número', 'Votos']]
        
        st.dataframe(df, use_container_width=True)
        
        # Gráfico de barras
        if len(candidatos) > 0:
            chart_data = pd.DataFrame({
                'Candidato': [f"{c[0]} ({c[1]})" for c in candidatos],
                'Votos': [c[3] for c in candidatos]
            })
            st.bar_chart(chart_data.set_index('Candidato'))

if __name__ == "__main__":
    main()