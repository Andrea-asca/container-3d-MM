import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from py3dbp import Packer, Bin, Item
import random

# Configurazione della pagina web
st.set_page_config(page_title="Container Optimizer 3D", layout="wide")

st.title("📦 Ottimizzatore Carico Container 3D")

# Inizializza la memoria a breve termine (Session State) per la coda di lavoro
if 'macchine' not in st.session_state:
    st.session_state.macchine = []

# --- INTERFACCIA: DIVISA IN DUE COLONNE ---
col1, col2 = st.columns([1, 2])

# COLONNA 1: INSERIMENTO DATI
with col1:
    st.header("1. Dimensioni Container")
    c_L = st.number_input("Lunghezza (asse X)", min_value=1.0, value=600.0)
    c_H = st.number_input("Altezza (asse Y)", min_value=1.0, value=250.0)
    c_P = st.number_input("Profondità (asse Z)", min_value=1.0, value=240.0)
    c_peso_max = st.number_input("Portata Massima (Peso)", min_value=1.0, value=24000.0)

    st.header("2. Aggiungi Macchinari")
    with st.form("form_macchina"):
        m_nome = st.text_input("Nome o ID Macchina")
        m_L = st.number_input("Lunghezza", min_value=1.0, value=100.0)
        m_H = st.number_input("Altezza", min_value=1.0, value=100.0)
        m_P = st.number_input("Profondità", min_value=1.0, value=100.0)
        m_peso = st.number_input("Peso Singolo", min_value=0.1, value=50.0)
        m_qty = st.number_input("Quantità", min_value=1, value=1)
        
        submit = st.form_submit_button("Aggiungi alla Coda")
        
        # Se premuto, salva la macchina in memoria
        if submit and m_nome:
            st.session_state.macchine.append({
                "Nome": m_nome,
                "L": m_L, "H": m_H, "P": m_P,
                "Peso": m_peso, "Quantità": m_qty,
                # Genera un colore esadecimale casuale per visualizzare i tipi di macchine
                "Colore": f"#{random.randint(0, 0xFFFFFF):06x}"
            })
            st.success(f"{m_qty}x {m_nome} aggiunta in coda!")

    if st.button("🗑 Svuota Coda", type="secondary"):
        st.session_state.macchine = []
        st.rerun()

# COLONNA 2: RISULTATI E 3D
with col2:
    st.header("3. Coda di Lavoro e Risultato")
    
    if len(st.session_state.macchine) > 0:
        # Mostra la tabella riassuntiva
        df = pd.DataFrame(st.session_state.macchine)
        st.dataframe(df.drop(columns=["Colore"]), use_container_width=True)
        
        # TASTO PRINCIPALE DI CALCOLO
        if st.button("🚀 Calcola Incastro Ottimizzato", type="primary"):
            with st.spinner("Il motore matematico sta ottimizzando i volumi..."):
                
                # 1. Setup del Risolutore
                packer = Packer()
                packer.add_bin(Bin('Container', c_L, c_H, c_P, c_peso_max))
                
                # 2. Espansione delle quantità (Unrolling)
                for mach in st.session_state.macchine:
                    for i in range(mach["Quantità"]):
                        # py3dbp ruota in automatico gli oggetti per trovare l'incastro migliore
                        packer.add_item(Item(
                            f"{mach['Nome']} _{i+1}", 
                            mach["L"], mach["H"], mach["P"], mach["Peso"]
                        ))
                        
                # 3. Esecuzione Calcolo
                packer.pack()
                container_usato = packer.bins[0]
                
                # 4. Configurazione Spazio 3D (Plotly)
                fig = go.Figure()
                
                # Disegna il telaio del Container
                x_c = [0, c_L, c_L, 0, 0, 0, c_L, c_L, 0, 0, c_L, c_L, c_L, c_L, 0, 0]
                y_c = [0, 0, c_H, c_H, 0, 0, 0, c_H, c_H, 0, 0, 0, c_H, c_H, c_H, c_H]
                z_c = [0, 0, 0, 0, 0, c_P, c_P, c_P, c_P, c_P, c_P, 0, 0, c_P, c_P, 0]
                
                fig.add_trace(go.Scatter3d(
                    x=x_c, y=y_c, z=z_c,
                    mode='lines', name='Container',
                    line=dict(color='black', width=3)
                ))
                
                # Funzione geometrica per creare un solido (Macchina)
                def add_box(fig, x, y, z, w, h, d, name, color):
                    # Superfici
                    fig.add_trace(go.Mesh3d(
                        x=[x, x+w, x+w, x, x, x+w, x+w, x],
                        y=[y, y, y+h, y+h, y, y, y+h, y+h],
                        z=[z, z, z, z, z+d, z+d, z+d, z+d],
                        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                        opacity=0.8, color=color, name=name, flatshading=True
                    ))
                    # Bordi neri per evidenziare i contorni
                    xp = [x, x+w, x+w, x, x, x, x+w, x+w, x, x, x+w, x+w, x+w, x+w, x, x]
                    yp = [y, y, y+h, y+h, y, y, y, y+h, y+h, y, y, y, y+h, y+h, y+h, y+h]
                    zp = [z, z, z, z, z, z+d, z+d, z+d, z+d, z+d, z+d, z, z, z+d, z+d, z]
                    fig.add_trace(go.Scatter3d(
                        x=xp, y=yp, z=zp, mode='lines',
                        line=dict(color='black', width=2),
                        showlegend=False, hoverinfo='none'
                    ))

                # 5. Estrazione coordinate e Rendering delle macchine caricate
                fitted_volume = 0
                for item in container_usato.items:
                    # Associa il colore corretto leggendo l'inizio del nome
                    base_name = item.name.split(" _")[0]
                    color = next((m["Colore"] for m in st.session_state.macchine if m["Nome"] == base_name), "#336699")
                    
                    # Coordinate [X, Y, Z] calcolate dal motore
                    pos = item.position
                    # Dimensioni [L, H, P] dopo l'eventuale rotazione dell'algoritmo
                    dim = item.get_dimension()
                    add_box(fig, float(pos[0]), float(pos[1]), float(pos[2]), 
                            float(dim[0]), float(dim[1]), float(dim[2]), item.name, color)
                    
                    fitted_volume += float(item.get_volume())

                container_volume = float(container_usato.get_volume())
                fill_percentage = (fitted_volume / container_volume) * 100

                # Impostazioni visuale della telecamera 3D
                fig.update_layout(
                    scene=dict(
                        xaxis=dict(title='X (Lunghezza)'),
                        yaxis=dict(title='Y (Altezza)'),
                        zaxis=dict(title='Z (Profondità)'),
                        aspectmode='data'
                    ),
                    margin=dict(l=0, r=0, b=0, t=0),
                    height=600
                )
                
                # Renderizza a schermo
                st.plotly_chart(fig, use_container_width=True)
                
                # Pannello delle Metriche Finali
                st.success(f"✅ Macchine imballate: {len(container_usato.items)}")
                if len(container_usato.unfitted_items) > 0:
                    st.error(f"❌ Macchine NON imballate (Spazio/Peso insufficiente): {len(container_usato.unfitted_items)}")
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Volume Occupato", f"{fill_percentage:.1f}%")
                col_m2.metric("Peso Totale", f"{container_usato.get_total_weight()} / {c_peso_max}")

    else:
        st.info("💡 Inizia aggiungendo le misure del container e le macchine dal pannello di sinistra.")
