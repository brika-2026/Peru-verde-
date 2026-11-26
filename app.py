import json, unicodedata, urllib.parse
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Perú Verde", page_icon="🌿", layout="wide")
D = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
DEPS, T, IC, ITEMS = D["deps"], D["T"], D["IC"], D["items"]
PE = "Por confirmar en la fuente oficial"

def norm(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

def blob(x):
    return norm(" ".join([x["n"], x["s"], " ".join(x["d"]), " ".join(map(str, x["f"].values())), T[x["t"]]]))

def photo(n):
    return "https://commons.wikimedia.org/w/index.php?search=" + urllib.parse.quote(n.split("(")[0] + " Perú") + "&ns6=1"

def ficha(x, key):
    with st.expander(f'{IC[x["t"]]} {x["n"]}  ·  {T[x["t"]]}'):
        st.write(x["s"])
        for k, v in x["f"].items():
            st.markdown(f"**{k}:** {v}")
        if x["d"]:
            st.markdown("**Departamentos:** " + ", ".join(x["d"]))
        if x["ll"]:
            st.map(pd.DataFrame([{"lat": x["ll"][0], "lon": x["ll"][1]}]), zoom=6, height=220)
        st.caption(f"Campos no listados: {PE}.")
        links = [f"[{a}]({b})" for a, b in x["src"]] + [f"[📷 Fotografías]({photo(x['n'])})"]
        st.markdown("**Fuentes:** " + " · ".join(links))

def show(items, prefix):
    if not items:
        st.info("Sin resultados. Esta información puede estar aún por incorporar.")
    for i, x in enumerate(items):
        ficha(x, f"{prefix}{i}")

st.sidebar.title("🌿 Perú Verde")
pages = ["Inicio", "Departamentos", *T.keys(), "Mapa"]
labels = {"Inicio": "🏠 Inicio", "Departamentos": "🗺️ Departamentos", "Mapa": "📍 Mapa interactivo",
          **{k: f"{IC[k]} {v}" for k, v in T.items()}}
page = st.sidebar.radio("Navegación", pages, format_func=labels.get)
st.sidebar.caption("Proyecto educativo. Verifica en las fuentes oficiales enlazadas.")

if page == "Inicio":
    st.title("Enciclopedia ambiental del Perú")
    st.write("Biodiversidad, recursos, áreas protegidas, normativa e instituciones de los 24 departamentos y el Callao.")
    q = norm(st.text_input("🔎 Busca una especie, lugar, ley, institución…"))
    if len(q) >= 2:
        r = [x for x in ITEMS if q in blob(x)]
        st.subheader(f"{len(r)} resultados")
        for t in T:
            g = [x for x in r if x["t"] == t]
            if g:
                st.markdown(f"### {IC[t]} {T[t]}")
                show(g, f"s{t}")
    else:
        cols = st.columns(4)
        for i, t in enumerate(T):
            cols[i % 4].metric(f"{IC[t]} {T[t]}", sum(x["t"] == t for x in ITEMS))

elif page == "Departamentos":
    st.title("Explorador por departamentos")
    d = st.selectbox("Departamento", list(DEPS))
    r = [x for x in ITEMS if d in x["d"]]
    pts = [{"lat": DEPS[d][0], "lon": DEPS[d][1]}] + [{"lat": x["ll"][0], "lon": x["ll"][1]} for x in r if x["ll"]]
    st.map(pd.DataFrame(pts), zoom=6, height=300)
    for t in T:
        g = [x for x in r if x["t"] == t]
        if g:
            st.markdown(f"### {IC[t]} {T[t]}")
            show(g, f"d{t}")
    st.info("Se muestra lo ya incorporado a la base de datos; complétalo con las fuentes oficiales.")
    st.markdown("[SINIA](https://sinia.minam.gob.pe) · [SERNANP](https://www.gob.pe/sernanp) · "
                f"[📷 Fotografías]({photo(d)})")

elif page == "Mapa":
    st.title("Mapa interactivo")
    c1, c2 = st.columns([1, 2])
    d = c1.selectbox("Departamento", ["Todos", *DEPS])
    ts = c2.multiselect("Categorías", [t for t in T if any(x["ll"] and x["t"] == t for x in ITEMS)],
                        default=[t for t in T if any(x["ll"] and x["t"] == t for x in ITEMS)], format_func=T.get)
    r = [x for x in ITEMS if x["ll"] and x["t"] in ts and (d == "Todos" or d in x["d"])]
    if r:
        st.map(pd.DataFrame([{"lat": x["ll"][0], "lon": x["ll"][1]} for x in r]), zoom=5 if d == "Todos" else 7)
        st.dataframe(pd.DataFrame([{"Nombre": x["n"], "Categoría": T[x["t"]], "Departamentos": ", ".join(x["d"])} for x in r]),
                     hide_index=True, use_container_width=True)
        sel = st.selectbox("Abrir ficha", [x["n"] for x in r])
        ficha(next(x for x in r if x["n"] == sel), "m")
    else:
        st.info("Sin puntos para este filtro.")

else:
    st.title(f"{IC[page]} {T[page]}")
    c1, c2 = st.columns(2)
    q = norm(c1.text_input("Filtrar…"))
    d = c2.selectbox("Departamento", ["Todos", *DEPS])
    show([x for x in ITEMS if x["t"] == page and q in blob(x) and (d == "Todos" or d in x["d"])], page)
