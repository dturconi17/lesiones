import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import json
from pathlib import Path

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #f5dce8;
}

details {
    background-color: white;
    border-radius: 8px;
    padding: 5px;
    margin-bottom: 8px;
}

summary {
    font-size: 16px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

/* FONDO PRINCIPAL */
.stApp {
    background-color: #f5f5f5;  /* o el color que quieras */
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #f5dce8;
}

/* TEXTO GENERAL */
h1, h2, h3, h4, h5, h6, p, span {
    color: #111827;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stMetricValue"] {
    color: #111827;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# CONFIG
# ======================================================

# ==============================
# CARGA Y PROCESAMIENTO NÓRDICO
# ==============================
@st.cache_data
def cargar_nordico():

    df = pd.read_excel("df_Nordico_final.xlsx")
    df.columns = df.columns.str.strip()

    # -----------------------------
    # FECHA
    # -----------------------------
    df["Date UTC"] = pd.to_datetime(
        df["Date UTC"],
        errors="coerce"
    )

    # -----------------------------
    # LIMPIEZA DNI
    # -----------------------------
    df["DNI"] = (
        df["DNI"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
    )

    # -----------------------------
    # ASEGURAR NUMÉRICOS
    # -----------------------------
    cols_numericas = [
        "L Reps", "R Reps",
        "L Max Force (N)", "R Max Force (N)",
        "L Max Torque (Nm)", "R Max Torque (Nm)",
        "L Avg Force (N)", "R Avg Force (N)",
        "L Max Impulse (Ns)", "R Max Impulse (Ns)",
        "Max Imbalance (%)", "Avg Imbalance (%)", "Impulse Imbalance (%)"
    ]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # RECALCULAR IMBALANCE (si falta)
    # -----------------------------
    mask_imbalance = df["Max Imbalance (%)"].isna()

    df.loc[mask_imbalance, "Max Imbalance (%)"] = (
        abs(df["L Max Force (N)"] - df["R Max Force (N)"]) /
        ((df["L Max Force (N)"] + df["R Max Force (N)"]) / 2)
    ) * 100

    mask_avg = df["Avg Imbalance (%)"].isna()

    df.loc[mask_avg, "Avg Imbalance (%)"] = (
        abs(df["L Avg Force (N)"] - df["R Avg Force (N)"]) /
        ((df["L Avg Force (N)"] + df["R Avg Force (N)"]) / 2)
    ) * 100

    # -----------------------------
    # FEATURE ENGINEERING (clave 🔥)
    # -----------------------------
    df["Force Total"] = df["L Max Force (N)"] + df["R Max Force (N)"]
    df["Force Diff"] = df["L Max Force (N)"] - df["R Max Force (N)"]

    df["Dominant Side"] = df["Force Diff"].apply(
        lambda x: "Izquierda" if x > 0 else ("Derecha" if x < 0 else "Balanceado")
    )

    return df



@st.cache_data
def load_users():
    return pd.read_excel("usuarios.xlsx")


def autenticar(usuario, password, df_users):
    user = df_users[
        (df_users["usuario"] == usuario) &
        (df_users["password"] == password)
    ]
    if not user.empty:
        return user.iloc[0]
    return None


DATA_PATH = Path("df_juveniles.json")
LESIONES_PATH = "df_lesiones.json"

# ======================================================
# FUNCIONES
# ======================================================
import json
import pandas as pd

def cargar_maestro_jugadores(path="df_juveniles.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data["maestro_jugadores"])

    # Tipos seguros
    df["dni"] = df["dni"].astype(str)

    df["nacimiento"] = pd.to_datetime(
        df["nacimiento"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    return df




def guardar_jugadores(df):
    df_guardar = df.copy()

    # 🔹 Convertir Timestamp → string
    if "nacimiento" in df_guardar.columns:
        df_guardar["nacimiento"] = df_guardar["nacimiento"].apply(
            lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else None
        )

    data = {
        "maestro_jugadores": df_guardar.to_dict(orient="records")
    }

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
# -----------------------------
# Estado de sesión
# -----------------------------
if "logueado" not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = None

df_users = load_users()

if not st.session_state.logueado:

    st.title("Login")

    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Password", type="password")

    if st.button("Ingresar"):
        user = autenticar(usuario_input, password_input, df_users)

        if user is not None:
            st.session_state.logueado = True
            st.session_state.usuario = user
            st.success(f"Bienvenidos {user['nombre']}")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()  # 🔴 corta la ejecución si no está logueado





# ======================================================
# SESSION STATE
# ======================================================
if "vista" not in st.session_state:
    st.session_state.vista = "dashboard"

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:

    # --- LOGOS ---
    st.image("sdc.png", use_container_width=True)
    st.image("huracan-removebg-preview.png", width=100)

    st.markdown("---")

    # --- HOME ---
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.vista = "home"

    # =========================
    # 📥 CARGA DE DATOS
    # =========================
    with st.expander("📥 Carga de datos", expanded=False):

        if st.button("🩹 Lesiones", use_container_width=True):
            st.session_state.vista = "lesiones"

        if st.button("📏 Antropometría", use_container_width=True):
            st.session_state.vista = "carga_antro"

        if st.button("🏋️ Nórdico", use_container_width=True):
            st.session_state.vista = "carga_nordico"

    # =========================
    # 📘 DESCRIPCIÓN
    # =========================
    with st.expander("📘 Análisis descriptivo", expanded=False):

        if st.button("Lesiones", use_container_width=True):
            st.session_state.vista = "descripcion"

        if st.button("Antropometría", use_container_width=True):
            st.session_state.vista = "descripcion_antro"

        if st.button("Nórdico", use_container_width=True):
            st.session_state.vista = "descripcion_nordico"

    # =========================
    # 📊 ANÁLISIS AVANZADO
    # =========================
    with st.expander("📊 Análisis avanzado", expanded=False):

        col1, col2 = st.columns(2)

        with col1:
            if st.button("2x2", use_container_width=True):
                st.session_state.vista = "matriz"

        with col2:
            if st.button("3x3", use_container_width=True):
                st.session_state.vista = "matriz3x3"

    # =========================
    # ⚽ JUGADORES
    # =========================
    with st.expander("⚽ Jugadores", expanded=False):

        if st.button("Maestro", use_container_width=True):
            st.session_state.vista = "Jugadores"

        if st.button("Pesaje", use_container_width=True):
            st.session_state.vista = "pesos"

        if st.button("Visión jugador", use_container_width=True):
            st.session_state.vista = "vision"

    # =========================
    # ⚙️ CONFIGURACION
    # =========================
    with st.expander("⚙️ Configuracion", expanded=False):

        if st.button("ABM Usuarios", use_container_width=True):
            st.session_state.vista = "abm_usuarios"
        if st.button("ABM Lesiones", use_container_width=True):
            st.session_state.vista = "abm_lesiones"            

    # --- FOOTER ---
    st.markdown("---")
    st.caption("v1.0 | Sports Data App")

# ======================================================
# CARGA DE DATOS
# ======================================================
@st.cache_data
def load_data():
    with open("df_lesiones.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return pd.DataFrame(data["lesiones"])

# 👉 ACÁ FALTABA ESTO
df = load_data()



def clasificar_variables(df):
    
    diccionario = {}

    for col in df.columns:

        col_lower = col.lower()

        # 1️⃣ Identificadores
        if col_lower in ["nombre", "nombre_cleaned", "dni"]:
            diccionario[col] = "identificador"

        # 2️⃣ Fechas
        elif "fecha" in col_lower:
            diccionario[col] = "fecha"

        # 3️⃣ Porcentajes (por nombre)
        elif "%" in col:
            diccionario[col] = "numerica_porcentaje"

        # 4️⃣ Variables en Kg o pliegues
        elif "kg" in col_lower or "pl" in col_lower:
            diccionario[col] = "numerica_continua"

        # 5️⃣ Variables antropométricas típicas
        elif col_lower in ["peso", "talla", "imc", "edad", "mo", "imo"]:
            diccionario[col] = "numerica_continua"

        # 6️⃣ Categoría y puesto
        elif col_lower in ["categoria", "puesto"]:
            diccionario[col] = "categorica"

        # 7️⃣ Fallback automático por contenido
        else:
            if pd.api.types.is_numeric_dtype(df[col]):
                diccionario[col] = "numerica_continua"
            else:
                diccionario[col] = "categorica"

    return diccionario

def dashboard_variable(df, columna, tipo_variable):
    
    st.markdown(f"## 📊 Dashboard Avanzado — {columna}")

    serie = df[columna]

    # -----------------------------
    # SOLO NUMÉRICAS
    # -----------------------------
    if tipo_variable in ["numerica_continua", "numerica_porcentaje"]:

        serie_limpia = (
            serie.astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("%", "", regex=False)
        )

        serie_num = pd.to_numeric(serie_limpia, errors="coerce").dropna()

        if len(serie_num) == 0:
            st.warning("No hay datos numéricos válidos.")
            return

        # -----------------------------
        # KPIs PRINCIPALES
        # -----------------------------
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Promedio", round(serie_num.mean(), 2))
        col2.metric("Mediana", round(serie_num.median(), 2))
        col3.metric("Mínimo", round(serie_num.min(), 2))
        col4.metric("Máximo", round(serie_num.max(), 2))

        # -----------------------------
        # PERCENTILES
        # -----------------------------
        p25 = serie_num.quantile(0.25)
        p50 = serie_num.quantile(0.50)
        p75 = serie_num.quantile(0.75)

        st.markdown("### 📈 Percentiles")
        colp1, colp2, colp3 = st.columns(3)
        colp1.metric("P25", round(p25, 2))
        colp2.metric("P50", round(p50, 2))
        colp3.metric("P75", round(p75, 2))

        # -----------------------------
        # BOXPLOT
        # -----------------------------
        fig1, ax1 = plt.subplots()
        ax1.boxplot(serie_num)
        ax1.set_title("Distribución (Boxplot)")
        st.pyplot(fig1)

        # -----------------------------
        # RANKING
        # -----------------------------
        ranking = (
            df[["Nombre", columna]]
            .copy()
        )

        ranking[columna] = pd.to_numeric(
            ranking[columna].astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("%", "", regex=False),
            errors="coerce"
        )

        ranking = ranking.dropna().sort_values(by=columna, ascending=False)

        ranking["Ranking"] = range(1, len(ranking) + 1)

        st.markdown("### 🏆 Ranking")
        st.dataframe(ranking.head(10))

        # -----------------------------
        # SEMÁFORO GENERAL
        # -----------------------------
        promedio = serie_num.mean()

        if promedio >= p75:
            st.success("🟢 Nivel alto (sobre P75)")
        elif promedio >= p50:
            st.info("🟡 Nivel medio (entre P50 y P75)")
        else:
            st.warning("🔴 Nivel bajo (debajo de P50)")

    # -----------------------------
    # CATEGÓRICAS
    # -----------------------------
    elif tipo_variable == "categorica":

        frecuencia = (
            serie.astype(str)
            .value_counts()
            .reset_index()
        )
        frecuencia.columns = [columna, "Cantidad"]

        st.metric("Cantidad total", serie.count())
        st.metric("Categorías únicas", serie.nunique())

        fig, ax = plt.subplots()
        ax.bar(frecuencia[columna], frecuencia["Cantidad"])
        plt.xticks(rotation=45)
        ax.set_title("Distribución")
        st.pyplot(fig)

        st.dataframe(frecuencia)



if st.session_state.vista == "descripcion_antro":
    
    st.title("📈 Distribución de variables Antropométricas")

    df_antro = pd.read_excel("df_antropometría_final.xlsx")

    # Diccionario automático de tipos
    dicc_variables = clasificar_variables(df_antro)

    # -----------------------------
    # Selector de CATEGORÍA
    # -----------------------------
    categorias_disponibles = (
        df_antro["Categoría"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    categorias_disponibles = sorted(categorias_disponibles)

    opciones_categoria = ["Todas las Categorías"] + categorias_disponibles

    categoria_seleccionada = st.selectbox(
        "Seleccioná la categoría",
        opciones_categoria
    )

    if categoria_seleccionada == "Todas las Categorías":
        df_filtrado = df_antro.copy()
    else:
        df_filtrado = df_antro[
            df_antro["Categoría"].astype(str) == categoria_seleccionada
        ]

    # -----------------------------
    # Selector de VARIABLE
    # -----------------------------
    columnas_excluidas = [
        'FECHA NAC','Nombre_cleaned','Nombre',
        'PUESTO','FECHAVAL','DNI'
    ]

    columnas_mostrables = [
        col for col in df_filtrado.columns
        if col not in columnas_excluidas
    ]

    columna = st.selectbox(
        "Seleccioná una variable",
        columnas_mostrables
    )

    ver = st.button("Ver dashboard")

    # -----------------------------
    # DASHBOARD DINÁMICO
    # -----------------------------
    if ver:

        tipo_variable = dicc_variables[columna]

        st.info(f"Tipo de variable detectado: **{tipo_variable}**")

        dashboard_variable(df_filtrado, columna, tipo_variable)    

elif st.session_state.vista == "carga_antro":
    
    import streamlit as st
    import pandas as pd
    import json
    from datetime import date
    import os

    st.title("📏 Carga Antropométrica")

    ANTRO_PATH = "df_antropometría_final.xlsx"

    # ==============================
    # INPUT DNI
    # ==============================
    dni = st.text_input("Documento del jugador")
    validar = st.button("Validar jugador")

    # ==============================
    # INIT SESSION
    # ==============================
    if "jugador_valido" not in st.session_state:
        st.session_state.jugador_valido = "no_validado"

    # ==============================
    # VALIDACIÓN
    # ==============================
    if validar:

        with open("df_juveniles.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        df_jug = pd.DataFrame(data["maestro_jugadores"])
        df_jug["dni"] = df_jug["dni"].astype(str)

        jugador = df_jug[df_jug["dni"] == dni]

        if jugador.empty:
            st.session_state.jugador_valido = None
        else:
            st.session_state.jugador_valido = jugador.iloc[0].to_dict()

    # ==============================
    # RECUPERAR ESTADO
    # ==============================
    jugador = st.session_state.get("jugador_valido")

    # ==============================
    # UI
    # ==============================
    if jugador == "no_validado":

        st.info("Ingresá un DNI y validá el jugador")

    elif jugador is None:

        st.warning("⚠️ El jugador no está registrado")

        if dni != "":
            if st.button("➕ Agregar Jugador al Maestro"):
                st.session_state.ir_a_jugadores = True

    else:

        nombre_jugador = jugador["nombre"]
        st.success(f"Jugador encontrado: {nombre_jugador}")

        # ==============================
        # FORMULARIO ANTROPOMETRÍA
        # ==============================
        with st.form("form_antro"):

            fecha = st.date_input("Fecha evaluación", value=date.today())

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                peso = st.number_input("Peso (kg)", min_value=0.0)
                talla = st.number_input("Talla (cm)", min_value=0.0)

            with col2:
                imc = st.number_input("IMC", min_value=0.0)
                edad = st.number_input("Edad", min_value=0)

            with col3:
                ma_pct = st.number_input("MA (%)", min_value=0.0)
                ma_kg = st.number_input("MA (kg)", min_value=0.0)

            with col4:
                mm_pct = st.number_input("MM (%)", min_value=0.0)
                mm_kg = st.number_input("MM (kg)", min_value=0.0)

            col5, col6, col7, col8 = st.columns(4)

            with col5:
                oseo_pct = st.number_input("% Óseo", min_value=0.0)

            with col6:
                mo = st.number_input("MO", min_value=0.0)

            with col7:
                imo = st.number_input("IMO", min_value=0.0)

            with col8:
                sum_pl = st.number_input("Sum 6 pl", min_value=0.0)

            submit = st.form_submit_button("Guardar medición")

        # ==============================
        # GUARDADO
        # ==============================
        if submit:

            try:

                if os.path.exists(ANTRO_PATH):
                    df_antro = pd.read_excel(ANTRO_PATH)
                else:
                    df_antro = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Nombre": nombre_jugador,
                    "DNI": dni,
                    "FECHEVAL": pd.to_datetime(fecha),
                    "PESO": peso,
                    "TALLA": talla,
                    "IMC": imc,
                    "EDAD": edad,
                    "MA (%)": ma_pct,
                    "MA (Kg)": ma_kg,
                    "MM (%)": mm_pct,
                    "MM (Kg)": mm_kg,
                    "%OSEO": oseo_pct,
                    "MO": mo,
                    "IMO": imo,
                    "Sum 6 pl": sum_pl
                }])

                df_antro = pd.concat([df_antro, nueva_fila], ignore_index=True)

                df_antro.to_excel(ANTRO_PATH, index=False)

                st.success("✅ Antropometría guardada correctamente")

            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

    # ==============================
    # REDIRECCIÓN
    # ==============================
    if st.session_state.get("ir_a_jugadores", False):

        st.session_state.vista = "Jugadores"
        st.session_state.ir_a_jugadores = False
        st.rerun()

elif st.session_state.vista == "descripcion_nordico":
    
    st.title("🏋️ Distribución de variables - Test Nórdico")

    df_nordico = pd.read_excel("df_Nordico_final.xlsx")

    # -----------------------------
    # LIMPIEZA INICIAL
    # -----------------------------
    df_nordico["Date UTC"] = pd.to_datetime(df_nordico["Date UTC"], errors="coerce")

    # Diccionario automático de tipos
    dicc_variables = clasificar_variables(df_nordico)

    # -----------------------------
    # Selector de JUGADOR
    # -----------------------------
    jugadores = (
        df_nordico["Nombre"]
        .dropna()
        .unique()
        .tolist()
    )

    jugadores = sorted(jugadores)

    opciones_jugador = ["Todos los jugadores"] + jugadores

    jugador_seleccionado = st.selectbox(
        "Seleccioná el jugador",
        opciones_jugador
    )

    if jugador_seleccionado == "Todos los jugadores":
        df_filtrado = df_nordico.copy()
    else:
        df_filtrado = df_nordico[
            df_nordico["Nombre"] == jugador_seleccionado
        ]

    # -----------------------------
    # Selector de TEST
    # -----------------------------
    tests = (
        df_filtrado["Test"]
        .dropna()
        .unique()
        .tolist()
    )

    tests = sorted(tests)

    test_seleccionado = st.selectbox(
        "Seleccioná el test",
        tests
    )

    df_filtrado = df_filtrado[
        df_filtrado["Test"] == test_seleccionado
    ]

    # -----------------------------
    # Selector de VARIABLE
    # -----------------------------
    columnas_excluidas = [
        "Name",
        "Nombre",
        "DNI",
        "Date UTC",
        "Time UTC",
        "Device",
        "Test"
    ]

    columnas_mostrables = [
        col for col in df_filtrado.columns
        if col not in columnas_excluidas
    ]

    columna = st.selectbox(
        "Seleccioná una variable",
        columnas_mostrables
    )

    ver = st.button("Ver dashboard")

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    if ver:

        tipo_variable = dicc_variables[columna]

        st.info(f"Tipo de variable detectado: **{tipo_variable}**")

        dashboard_variable(df_filtrado, columna, tipo_variable)

# ======================================================
# VISTA: DESCRIPCIÓN DE VARIABLES
# ======================================================
if st.session_state.vista == "descripcion":

    st.title("📈 Distribución de variables")

    # -----------------------------
    # Selector de AÑO
    # -----------------------------
    anios_disponibles = (
        df["tipo"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    anios_disponibles = sorted(anios_disponibles)

    opciones_anio = ["Todos los años"] + anios_disponibles

    anio_seleccionado = st.selectbox(
        "Seleccioná el año",
        opciones_anio
    )

    if anio_seleccionado == "Todos los años":
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df["año"] == anio_seleccionado]


    # -----------------------------
    # Selectores principales
    # -----------------------------
    columnas_excluidas = [
        'dni'
    ]

    columnas_mostrables = [
        col for col in df_filtrado.columns
        if col not in columnas_excluidas
    ]
    
    columna = st.selectbox(
    "Seleccioná una variable",
    columnas_mostrables
    )

    metrica = st.selectbox(
        "Seleccioná la métrica",
        ["Cantidad", "Promedio", "Mínimo", "Máximo"]
    )

    ver = st.button("Ver")


    # -----------------------------
    # LÓGICA GENERAL
    # -----------------------------
    if ver:

        st.subheader(
            f"Distribución de {columna} – {metrica} ({anio_seleccionado})"
        )

        # -------- CATEGÓRICO --------
        if df_filtrado[columna].dtype == "object":

            if metrica != "Cantidad":
                st.warning("Para variables categóricas solo se puede mostrar Cantidad.")
            else:
                data_plot = (
                    df_filtrado[columna]
                    .value_counts(dropna=False)
                    .reset_index()
                )
                data_plot.columns = [columna, "Cantidad"]

                fig, ax = plt.subplots()
                ax.bar(data_plot[columna].astype(str), data_plot["Cantidad"])
                ax.set_xlabel(columna)
                ax.set_ylabel("Cantidad")
                plt.xticks(rotation=90, ha="right", fontsize=7)

                st.pyplot(fig)

        # -------- NUMÉRICO --------
        else:
            if metrica == "Cantidad":
                valor = df_filtrado[columna].count()
            elif metrica == "Promedio":
                valor = df_filtrado[columna].mean()
            elif metrica == "Mínimo":
                valor = df_filtrado[columna].min()
            elif metrica == "Máximo":
                valor = df_filtrado[columna].max()

            st.metric(label=metrica, value=round(valor, 2))

    # ======================================================
    # MAPA CORPORAL DETALLADO
    # ======================================================
    if ver and columna == "zona_cuerpo":

        st.subheader("🧍 Mapa corporal de lesiones")

        df_zonas = (
            df_filtrado
            .groupby("zona_cuerpo")
            .size()
            .reset_index(name="cantidad")
        )

        coordenadas_cuerpo = {
            "Cabeza /Cara": (0.2, 0.1),
            "Muslo posterior": (0.15, 0.55),
            "Rodilla": (0.15, 0.7),
            "Tobillo": (0.15, 0.9),
            "Muslo anterior": (0.5, 0.55),
            "Muslo medial": (0.85, 0.60),
            "Pierna/Aquiles": (0.82, 0.85),
            "Pie": (0.85, 1),
            "Codo": (0.45, 0.4),
            "Cadera": (0.85, 0.45),
        }

        img = mpimg.imread("cuerpo_humano.jpg")

        fig, ax = plt.subplots(figsize=(6, 10))
        ax.imshow(img)
        ax.axis("off")

        for _, row in df_zonas.iterrows():
            zona = row["zona_cuerpo"]
            cantidad = row["cantidad"]

            if zona in coordenadas_cuerpo:
                x, y = coordenadas_cuerpo[zona]
                ax.scatter(
                    x * img.shape[1],
                    y * img.shape[0],
                    s=cantidad * 20,
                    alpha=0.6,
                    edgecolors="black"
                )
                ax.text(
                    x * img.shape[1],
                    y * img.shape[0],
                    str(cantidad),
                    ha="center",
                    va="center",
                    fontsize=9
                )

        st.pyplot(fig)

    # ======================================================
    # MAPA CORPORAL AGRUPADO
    # ======================================================
    if ver and columna == "zona_cuerpo2":

        st.subheader("🧍 Mapa corporal de lesiones - Partes")

        df_zonas = (
            df_filtrado
            .groupby("zona_cuerpo2")
            .size()
            .reset_index(name="cantidad")
        )

        coordenadas_cuerpo = {
            "Tren Inferior": (0.22, 0.75),
            "Tren Superior": (0.50, 0.25),
            "Columna/Pelvis": (0.80, 0.40),
        }

        img = mpimg.imread("trenes.jpeg")

        fig, ax = plt.subplots(figsize=(6, 10))
        ax.imshow(img)
        ax.axis("off")

        for _, row in df_zonas.iterrows():
            zona = row["zona_cuerpo2"]
            cantidad = row["cantidad"]

            if zona in coordenadas_cuerpo:
                x, y = coordenadas_cuerpo[zona]
                ax.scatter(
                    x * img.shape[1],
                    y * img.shape[0],
                    s=cantidad * 20,
                    alpha=0.6,
                    edgecolors="black"
                )
                ax.text(
                    x * img.shape[1],
                    y * img.shape[0],
                    str(cantidad),
                    ha="center",
                    va="center",
                    fontsize=9
                )

        st.pyplot(fig)



# ======================================================
# VISTA: VARIABLES 2x2
# ======================================================
elif st.session_state.vista == "matriz":
    

    @st.cache_data
    def load_lesiones():
        with open("df_lesiones.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data["lesiones"])

        # 🔒 Limpieza defensiva
        df = df.loc[:, ~df.columns.duplicated()]

        return df

    df = load_lesiones()

    campos_excluidos = [
        "dni",
        "nombre",
        "tipo",
        "fecha_lesion",
        "nacimiento",
        "registro",
        "marca_temporal_nueva"
    ]

    st.subheader("📋 Reporte por Año, Campo 1 y Campo 2")

    campos_disponibles = [
        c for c in df.columns
        if c not in campos_excluidos
    ]

    col1, col2 = st.columns(2)

    with col1:
        campo_1 = st.selectbox(
            "Campo 1",
            campos_disponibles
        )

    with col2:
        campo_2 = st.selectbox(
            "Campo 2",
            [c for c in campos_disponibles if c != campo_1]
        )


    if campo_1 and campo_2:
        
        df_reporte = (
            df
            .groupby(
                ["tipo", campo_1, campo_2],
                as_index=False
            )
            .agg(cantidad=("dni", "count"))
            .sort_values(
                ["tipo", "cantidad"],
                ascending=[True, False]
            )
        )


    
    st.dataframe(df_reporte, width="stretch")

    st.subheader("📐 Vista matriz (pivot)")

    df_pivot = pd.pivot_table(
        df_reporte,
        index=[campo_1, campo_2],
        columns="tipo",
        values="cantidad",
        fill_value=0
    )

    st.dataframe(df_pivot, width="stretch")

elif st.session_state.vista == "matriz3x3":

    @st.cache_data
    def load_lesiones():
        with open("df_lesiones.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data["lesiones"])

        # 🔒 Limpieza defensiva
        df = df.loc[:, ~df.columns.duplicated()]

        return df

    df = load_lesiones()
    
    st.title("Reporte de Lesiones")

    # --- Validación mínima ---
    if "tipo" not in df.columns:
        st.error("El archivo debe tener el campo 'tipo' (año)")
        st.stop()

    # --- Columnas disponibles (excluimos tipo) ---
    columnas_disponibles = [c for c in df.columns if c != "tipo"]

    # --- Selectores ---
    col1, col2, col3 = st.columns(3)

    with col1:
        campo_1 = st.selectbox("Campo 1", columnas_disponibles)

    with col2:
        campo_2 = st.selectbox(
            "Campo 2",
            [c for c in columnas_disponibles if c != campo_1]
        )

    with col3:
        campo_3 = st.selectbox(
            "Campo 3",
            [c for c in columnas_disponibles if c not in [campo_1, campo_2]]
        )

    # --- Generar matriz ---
    df_grouped = (
        df
        .groupby(["tipo", campo_1, campo_2, campo_3])
        .size()
        .reset_index(name="cantidad")
    )

    matriz = df_grouped.pivot_table(
        index="tipo",
        columns=[campo_1, campo_2, campo_3],
        values="cantidad",
        fill_value=0
    )

    st.subheader("Matriz de Lesiones")
    st.dataframe(matriz)

        
elif st.session_state.vista == "Jugadores":
    
    st.title("👥 Maestro de Jugadores")

    st.markdown("""
    Acá podés **ver, editar y agregar jugadores**.  
    Los cambios se guardan directamente en el archivo base.
    """)

    # --- Cargar datos ---
    df_jugadores = cargar_maestro_jugadores()

    # --- Tipos seguros ---
    df_jugadores["dni"] = df_jugadores["dni"].astype(str)
    
        # --- Asegurar columnas nuevas ---
    if "telefono" not in df_jugadores.columns:
        df_jugadores["telefono"] = ""

    if "pierna_habil" not in df_jugadores.columns:
        df_jugadores["pierna_habil"] = "Sin Definir"

    # --- Editor ---
    df_editado = st.data_editor(
        df_jugadores,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "dni": st.column_config.TextColumn("DNI"),
            "nombre": st.column_config.TextColumn("Nombre"),
            "nacimiento": st.column_config.DateColumn(
                "Fecha de Nacimiento",
                format="DD/MM/YYYY"
            ),
            "obra_social": st.column_config.TextColumn("Obra Social"),
            "afiliado": st.column_config.TextColumn("Afiliado"),
            "telefono": st.column_config.TextColumn("Teléfono"),
            "pierna_habil": st.column_config.SelectboxColumn(
                "Pierna hábil",
                options=[
                    "Sin Definir",
                    "Derecha",
                    "Izquierda",
                    "Ambidiestro"
                ],
                required=False
            ),
        },
    )

    # --- Guardar cambios ---
    if st.button("💾 Guardar cambios"):
        guardar_jugadores(df_editado)
        st.success("✅ Cambios guardados correctamente")


elif st.session_state.vista == "home":
    st.title("👥 Quienes cumplen años")

    df = cargar_maestro_jugadores()

    df["nacimiento"] = pd.to_datetime(
        df["nacimiento"],
        format="%d/%m/%Y",
        errors="coerce"
    )
    
    hoy = pd.Timestamp.today().normalize()

    def ajustar_cumple(fecha):
        try:
            return fecha.replace(year=hoy.year)
        except ValueError:
            return fecha.replace(year=hoy.year, day=28)

    df["cumple_anio"] = df["nacimiento"].apply(
        lambda x: ajustar_cumple(x) if pd.notna(x) else pd.NaT
    )

    df.loc[df["cumple_anio"] < hoy, "cumple_anio"] += pd.DateOffset(years=1)

    df["dias_para_cumple"] = (df["cumple_anio"] - hoy).dt.days

    proximos = (
        df[df["dias_para_cumple"].between(0, 30)]
        .sort_values("dias_para_cumple")
    )

    if proximos.empty:
        st.info("🎉 No hay cumpleaños en los próximos días")
    else:
        st.markdown("### 👥 Jugadores que cumplen años pronto")

        st.dataframe(
            proximos[["nombre", "dni", "nacimiento", "dias_para_cumple"]]
            .rename(columns={
                "nombre": "Jugador",
                "dni": "DNI",
                "nacimiento": "Fecha de nacimiento",
                "dias_para_cumple": "Días para cumplir años"
            }),
            width="stretch",
            hide_index=True
        )


elif st.session_state.vista == "lesiones":
    
    import streamlit as st
    import os
    from datetime import date

    with open("parametros.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        
    st.title("🩹 Formulario para cargar lesiones")


    # ===========================
    
    dni = st.text_input("Documento del jugador")
    validar = st.button("Validar jugador")

    # ==============================
    # INIT SESSION STATE
    # ==============================
    if "jugador_valido" not in st.session_state:
        st.session_state.jugador_valido = "no_validado"

    # ==============================
    # VALIDACIÓN
    # ==============================
    if validar:

        with open("df_juveniles.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        df_jug = pd.DataFrame(data["maestro_jugadores"])
        df_jug["dni"] = df_jug["dni"].astype(str)

        jugador = df_jug[df_jug["dni"] == dni]

        if jugador.empty:
            st.session_state.jugador_valido = None
        else:
            st.session_state.jugador_valido = jugador.iloc[0].to_dict()

    # ==============================
    # RECUPERAR ESTADO
    # ==============================
    jugador = st.session_state.get("jugador_valido")

    # ==============================
    # UI
    # ==============================
    if jugador == "no_validado":
        st.info("Ingresá un DNI y validá el jugador")

    elif jugador is None:

        st.warning("⚠️ El jugador no está registrado")

        if dni != "":
            if st.button("➕ Agregar Jugador al Maestro"):
                st.session_state.ir_a_jugadores = True

    else:

        nombre_jugador = jugador["nombre"]
        st.success(f"Jugador encontrado: {nombre_jugador}")

        with st.form("form_lesiones"):

            # ======================
            # DATOS DEL JUGADOR
            # ======================
            
            categoria = st.selectbox("Categoría *", config["categorias"])
            division = st.selectbox("División con la que entrena *",config["divisiones"])
            posicion = st.selectbox("Posición en el campo de juego *",config["posiciones"])

            fecha_lesion = st.date_input(
                "Fecha de lesión",
                value=date.today(),
                format="DD/MM/YYYY"
            )

            definicion_lesion = st.selectbox("Definición de lesión *", config["definicion_lesiones"])
            donde_ocurrio = st.selectbox("Dónde ocurrió la lesión *", config["donde_ocurrios"])
            cual_trastorno = st.text_input("¿Cuál? (Sólo si seleccionó Trastorno deportivo no lesional)")
            campo_juego = st.selectbox("Campo de juego", config["campo_juegos"])
            cancha = st.selectbox("Cancha dónde se lesionó", config["canchas"])

            momento = st.selectbox(
                "Momento de la lesión",
                [
                    "Sin Definir",
                    "Durante un partido",
                    "Durante un entrenamiento"
                ]
            )

            sector_cuerpo = st.selectbox(
                "Sector de cuerpo afectado *",
                [
                    "Sin Definir",
                    "Tren Superior",
                    "Tren Inferior",
                    "Columna / Pelvis",
                    "No Aplica"
                ]
            )

            lado_cuerpo = st.selectbox(
                "Lado del cuerpo lesionado *",
                [
                    "Sin Definir",
                    "Derecho",
                    "Izquierdo",
                    "Bilateral",
                    "No aplica"
                ]
            )

    ###
            lugar_lesion = st.selectbox("Lugar de la Lesion",config["lugar_lesiones"])
            diagnostico1 = st.selectbox("Diagnostico 1",config["diagnosticos1"])
            diagnostico2 = st.text_input("Diagnostico 2 abierto a comentarios")
            tipo_lesion = st.selectbox("Tipo de Lesion",config["tipo_lesiones"])

            causa_lesion = st.selectbox(
                "Causa de la Lesion",
                [
                    "Sin Definir",
                    "No Traumatica",
                    "Traumatica"
                ]
            )

            modo_inicio = st.selectbox(
                "Modo de Inicio",
                [
                    "Sin Definir",
                    "Agudo",
                    "Agudo Repetitivo",
                    "Gradual Repetitivo"
                ]
            )

            accion_juego = st.selectbox("Accion de Juego",config["accion_juegos"])

            st.write("Requiere estudios complementarios")

            opciones = ["RX", "RMN", "TAC", "ECO"]
            estudios = []

            for op in opciones:
                if st.checkbox(op):
                    estudios.append(op)

            tipo_de_lesion = st.selectbox(
                "Tipo de Lesion",
                [
                    "Sin Definir",
                    "Time loss - Pierde dias de entrenamiento",
                    "Atencion medica - No pierde dias de entrenamiento"
                ]
            )

            tratamiento_inicial = st.selectbox(
                "Tratamiento Inicial",
                [
                    "Sin Definir",
                    "Inmovilizador",
                    "Conservador",
                    "Quirurgico"
                ]
            )

            tiempo_recuperacion = st.number_input(
                "Tiempo Estimado de Recuperacion",
                min_value=0,
                step=1
            )


            # ======================
            # SUBMIT
            # ======================
            submitted = st.form_submit_button("💾 Guardar lesión")

        if submitted:
            if dni == "" or categoria == "Sin Definir" or division == "Sin Definir"or posicion == "Sin Definir"or definicion_lesion == "Sin Definir" or donde_ocurrio == "Sin Definir" or cual_trastorno == "Sin Definir" or campo_juego == "Sin Definir" or cancha == "Sin Definir" or momento == "Sin Definir" or sector_cuerpo == "Sin Definir" or lado_cuerpo == "Sin Definir" or lugar_lesion == "Sin Definir" or diagnostico1 == "Sin Definir" or tipo_lesion == "Sin Definir" or causa_lesion == "Sin Definir" or modo_inicio == "Sin Definir" or accion_juego == "Sin Definir" or tipo_de_lesion == "Sin Definir" or tratamiento_inicial == "Sin Definir":
                st.error("⚠️ Completá los campos obligatorios")
            else:
                data_lesion = {
                    "tipo":"lesion 2026",
                    "dni": dni,
                    "categoria": categoria,
                    "division": division,
                    "posicion": posicion,
                    "fecha_lesion": fecha_lesion.strftime("%d/%m/%Y"),
                    "definicion_lesion": definicion_lesion,
                    "donde_ocurrio": donde_ocurrio,
                    "cual_trastorno": cual_trastorno,
                    "campo_juego": campo_juego,
                    "cancha": cancha,
                    "momento": momento,
                    "sector_cuerpo": sector_cuerpo,
                    "lado_cuerpo": lado_cuerpo,
                    "lugar_lesion":lugar_lesion,
                    "diagnostico1":diagnostico1,
                    "diagnostico2":diagnostico2,
                    "tipo_lesion":tipo_lesion,
                    "causa_lesion":causa_lesion,
                    "modo_inicio":modo_inicio,
                    "accion_juego":accion_juego,
                    "tipo_de_lesion":tipo_de_lesion,
                    "tratamiento_inicial":tratamiento_inicial,
                    "tiempo_recuperacion":tiempo_recuperacion,
                    "estudios": estudios
                }

                # 👉 Cargar JSON existente o crear estructura base
                if os.path.exists(LESIONES_PATH):
                    with open(LESIONES_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = {"lesiones": []}

                # 👉 Asegurar clave
                if "lesiones" not in data:
                    data["lesiones"] = []

                # 👉 Agregar lesión
                data["lesiones"].append(data_lesion)

                # 👉 Guardar
                with open(LESIONES_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                st.success("✅ Lesión guardada correctamente")
                
    if st.session_state.get("ir_a_jugadores", False):
    
        st.session_state.vista = "Jugadores"
        st.session_state.ir_a_jugadores = False
        st.rerun()                

elif st.session_state.vista == "pesos":
    st.title("⚖️ Análisis del Pesaje")

    df_long = pd.read_excel("df_pesos.xlsx")

    # Asegurar tipos correctos
    df_long["fecha"] = pd.to_datetime(df_long["fecha"], errors="coerce")
    df_long["peso"] = pd.to_numeric(df_long["peso"], errors="coerce")

    jugadores = sorted(df_long["JUGADOR"].unique())

    jugadores_sel = st.multiselect(
        "Seleccioná jugadores",
        jugadores,
        default=jugadores[:3]
    )

    df_plot = df_long[df_long["JUGADOR"].isin(jugadores_sel)]

    import plotly.express as px

    fig = px.line(
        df_plot,
        x="fecha",
        y="peso",
        color="JUGADOR",
        markers=True,
        title="Evolución del peso por jugador"
    )

    # ✅ AHORA sí: control del eje Y
    fig.update_yaxes(
        range=[60, 90],
        title="Peso (kg)"
    )

    fig.update_layout(
        xaxis_title="Fecha",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width="stretch")

    st.dataframe(df_plot)
    
elif st.session_state.vista == "vision":
    
    import plotly.express as px
    import plotly.graph_objects as go

    st.title("🧑‍⚽️ Player Dashboard")

    # ==============================
    # INPUT
    # ==============================
    dni = st.text_input("Ingresá el DNI del jugador")

    if not dni:
        st.stop()

    dni = str(dni).strip()

    # ==============================
    # CARGA DE DATOS
    # ==============================

    # ANTRO
    df_antro = pd.read_excel("df_antropometría_final.xlsx")
    df_antro.columns = df_antro.columns.str.strip()
    df_antro["FECHEVAL"] = pd.to_datetime(df_antro["FECHEVAL"], errors="coerce")

    mask_2025 = df_antro["FECHEVAL"].dt.year == 2025
    df_antro.loc[mask_2025, ["MA (%)", "MM (%)"]] *= 100

    mask = df_antro["%OSEO"].isna()
    df_antro.loc[mask, "masa_residual"] = df_antro.loc[mask, "PESO"] * 0.24
    df_antro.loc[mask, "masa_osea"] = df_antro.loc[mask, "PESO"] - (
        df_antro.loc[mask, "MA (Kg)"] +
        df_antro.loc[mask, "MM (Kg)"] +
        df_antro.loc[mask, "masa_residual"]
    )
    df_antro.loc[mask, "%OSEO"] = df_antro.loc[mask, "masa_osea"] / df_antro.loc[mask, "PESO"] * 100

    df_antro["DNI"] = df_antro["DNI"].astype(str).str.replace(r"\D", "", regex=True)
    antro_jug = df_antro[df_antro["DNI"] == dni].copy()

    # JUGADORES
    df_jug = pd.DataFrame(json.load(open("df_juveniles.json"))["maestro_jugadores"])
    df_jug["dni"] = df_jug["dni"].astype(str)

    # LESIONES
    df_les = pd.DataFrame(json.load(open("df_lesiones.json"))["lesiones"])
    df_les["dni"] = df_les["dni"].astype(str)

    # PESOS
    df_pesos = pd.read_excel("df_pesos.xlsx")
    df_pesos["dni"] = df_pesos["DNI"].fillna(0).astype(int).astype(str)

    # NÓRDICO
    df_nordico = cargar_nordico()

    # ==============================
    # VALIDACIÓN
    # ==============================
    jugador = df_jug[df_jug["dni"] == dni]

    if jugador.empty:
        st.warning("No se encontró el jugador")
        st.stop()

    lesiones_jug = df_les[df_les["dni"] == dni]
    pesos_jug = df_pesos[df_pesos["dni"] == dni].copy()
    pesos_jug["fecha"] = pd.to_datetime(pesos_jug["fecha"], errors="coerce")
    pesos_jug = pesos_jug.dropna(subset=["fecha"])

    # ANTRO
    if not antro_jug.empty:
        antro_jug = antro_jug.sort_values("FECHEVAL")
        ultimo_registro = antro_jug.iloc[-1]
    else:
        ultimo_registro = None

    # NORDICO
    nordico_jug = df_nordico[df_nordico["DNI"] == dni].copy()
    if not nordico_jug.empty:
        nordico_jug["Date UTC"] = pd.to_datetime(nordico_jug["Date UTC"], errors="coerce")
        nordico_jug = nordico_jug.sort_values("Date UTC")
        ultimo = nordico_jug.iloc[-1]
    else:
        ultimo = None

    # ==============================
    # HEADER
    # ==============================
    st.markdown(f"""
    ### {jugador.iloc[0]["nombre"]}
    📅 {jugador.iloc[0]["nacimiento"]} | 📞 {jugador.iloc[0]["telefono"]} | 🦵 {jugador.iloc[0]["pierna_habil"]}
    """)

    # ==============================
    # KPIs
    # ==============================
    st.markdown("## 📊 Indicadores clave")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🩹 Lesiones", len(lesiones_jug))

    if not pesos_jug.empty:
        col2.metric("⚖️ Peso", round(pesos_jug.iloc[-1]["peso"], 1))

    if ultimo_registro is not None:
        col3.metric("IMC", round(ultimo_registro["IMC"], 2))
        col4.metric("MM (%)", round(ultimo_registro["MM (%)"], 1))

    # ==============================
    # ESTADO GLOBAL
    # ==============================
    st.markdown("## 🚨 Estado del jugador")

    if ultimo is not None:
        imbalance = ultimo["Max Imbalance (%)"]

        if imbalance > 15:
            st.error("🔴 Alto riesgo físico")
        elif imbalance > 10:
            st.warning("🟠 Riesgo moderado")
        else:
            st.success("🟢 Buen estado físico")

    # ==============================
    # RADAR + SCORE
    # ==============================
    if ultimo_registro is not None and ultimo is not None:

        def norm(v, minv, maxv):
            return max(0, min(100, (v - minv) / (maxv - minv) * 100))

        variables = {
            "MM": norm(ultimo_registro["MM (%)"], 30, 60),
            "MA": norm(ultimo_registro["MA (%)"], 5, 25),
            "Óseo": norm(ultimo_registro["%OSEO"], 10, 20),
            "IMC": norm(ultimo_registro["IMC"], 18, 28),
            "Fuerza": norm(ultimo["L Max Force (N)"], 100, 400),
            "Balance": 100 - norm(ultimo["Max Imbalance (%)"], 0, 20)
        }

        categorias = list(variables.keys())
        valores = list(variables.values())

        # SCORE
        score = sum(valores) / len(valores)
        st.metric("⭐ Score general", round(score, 1))

        categorias += [categorias[0]]
        valores += [valores[0]]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name='Jugador'
        ))

        fig.add_trace(go.Scatterpolar(
            r=[60, 50, 55, 50, 65, 70, 60],
            theta=categorias,
            fill='toself',
            opacity=0.3,
            name='Promedio'
        ))

        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # PESO
    # ==============================
    st.markdown("## ⚖️ Evolución física")

    if not pesos_jug.empty:
        fig = px.line(pesos_jug, x="fecha", y="peso", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # ANTRO
    # ==============================
    if ultimo_registro is not None:
        st.markdown("## 📏 Perfil corporal")

        cols = st.columns(4)
        cols[0].metric("Peso", ultimo_registro["PESO"])
        cols[1].metric("Talla", ultimo_registro["TALLA"])
        cols[2].metric("IMC", round(ultimo_registro["IMC"], 2))
        cols[3].metric("Edad", ultimo_registro["EDAD"])

    # ==============================
    # NORDICO
    # ==============================
    if ultimo is not None:
        st.markdown("## 🏋️ Rendimiento")

        cols = st.columns(4)
        cols[0].metric("L Force", round(ultimo["L Max Force (N)"], 1))
        cols[1].metric("R Force", round(ultimo["R Max Force (N)"], 1))
        cols[2].metric("L Torque", round(ultimo["L Max Torque (Nm)"], 1))
        cols[3].metric("R Torque", round(ultimo["R Max Torque (Nm)"], 1))

    # ==============================
    # LESIONES
    # ==============================
    st.markdown("## 🩹 Historial médico")

    if lesiones_jug.empty:
        st.success("Sin lesiones")
    else:
        st.dataframe(lesiones_jug, use_container_width=True)

    # ==============================
    # HISTORIALES
    # ==============================
    with st.expander("Antropometría histórica"):
        st.dataframe(antro_jug)

    with st.expander("Nórdico histórico"):
        st.dataframe(nordico_jug)

                    
elif st.session_state.vista == "carga_nordico":
    
    import os
    import json
    import pandas as pd
    import streamlit as st

    st.title("🏋️ Carga Test Nórdico")

    dni = st.text_input("Documento del jugador")
    validar = st.button("Validar jugador")

    # ==============================
    # INIT SESSION STATE
    # ==============================
    if "jugador_valido" not in st.session_state:
        st.session_state.jugador_valido = "no_validado"

    # ==============================
    # VALIDACIÓN
    # ==============================
    if validar:

        with open("df_juveniles.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        df_jug = pd.DataFrame(data["maestro_jugadores"])
        df_jug["dni"] = df_jug["dni"].astype(str)

        jugador = df_jug[df_jug["dni"] == dni]

        if jugador.empty:
            st.session_state.jugador_valido = None
        else:
            st.session_state.jugador_valido = jugador.iloc[0].to_dict()

    # ==============================
    # RECUPERAR ESTADO
    # ==============================
    jugador = st.session_state.get("jugador_valido")

    # ==============================
    # UI
    # ==============================
    if jugador == "no_validado":
        st.info("Ingresá un DNI y validá el jugador")

    elif jugador is None:

        st.warning("⚠️ El jugador no está registrado")

        if dni != "":
            if st.button("➕ Agregar Jugador al Maestro"):
                st.session_state.ir_a_jugadores = True

    else:

        nombre_jugador = jugador["nombre"]
        st.success(f"Jugador encontrado: {nombre_jugador}")

        # ==============================
        # FORMULARIO NÓRDICO
        # ==============================
        with st.form("form_nordico"):

            fecha = st.date_input("Fecha del test")
            hora = st.time_input("Hora del test")

            device = st.text_input("Dispositivo")
            test = st.text_input("Tipo de test")

            col1, col2 = st.columns(2)

            with col1:
                l_reps = st.number_input("L Reps")
                l_max_force = st.number_input("L Max Force (N)")
                l_max_torque = st.number_input("L Max Torque (Nm)")
                l_avg_force = st.number_input("L Avg Force (N)")
                l_max_impulse = st.number_input("L Max Impulse (Ns)")

            with col2:
                r_reps = st.number_input("R Reps")
                r_max_force = st.number_input("R Max Force (N)")
                r_max_torque = st.number_input("R Max Torque (Nm)")
                r_avg_force = st.number_input("R Avg Force (N)")
                r_max_impulse = st.number_input("R Max Impulse (Ns)")

            max_imbalance = st.number_input("Max Imbalance (%)")
            avg_imbalance = st.number_input("Avg Imbalance (%)")
            impulse_imbalance = st.number_input("Impulse Imbalance (%)")

            submit = st.form_submit_button("Guardar medición")

        # ==============================
        # GUARDADO (FUERA DEL FORM)
        # ==============================
        if submit:

            try:
                st.write("DEBUG: entrando al submit")
                st.write("Path actual:", os.getcwd())

                df_nordico = pd.read_excel("df_Nordico_final.xlsx")

                nueva_fila = pd.DataFrame([{
                    "Name": nombre_jugador,
                    "Nombre": nombre_jugador,
                    "DNI": dni,
                    "Date UTC": pd.to_datetime(fecha),
                    "Time UTC": hora,
                    "Device": device,
                    "Test": test,
                    "L Reps": l_reps,
                    "R Reps": r_reps,
                    "L Max Force (N)": l_max_force,
                    "R Max Force (N)": r_max_force,
                    "Max Imbalance (%)": max_imbalance,
                    "L Max Torque (Nm)": l_max_torque,
                    "R Max Torque (Nm)": r_max_torque,
                    "L Avg Force (N)": l_avg_force,
                    "R Avg Force (N)": r_avg_force,
                    "Avg Imbalance (%)": avg_imbalance,
                    "L Max Impulse (Ns)": l_max_impulse,
                    "R Max Impulse (Ns)": r_max_impulse,
                    "Impulse Imbalance (%)": impulse_imbalance
                }])

                st.write("Filas antes:", len(df_nordico))

                df_nordico = pd.concat([df_nordico, nueva_fila], ignore_index=True)

                st.write("Filas después:", len(df_nordico))

                df_nordico.to_excel("df_Nordico_final.xlsx", index=False)

                st.success("✅ Test nórdico guardado correctamente")

            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

    # ==============================
    # REDIRECCIÓN (SIEMPRE AL FINAL)
    # ==============================
    if st.session_state.get("ir_a_jugadores", False):

        st.session_state.vista = "Jugadores"
        st.session_state.ir_a_jugadores = False
        st.rerun()