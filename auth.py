"""
Sistema de autenticação do Dashboard GWM.

Cada usuário tem:
  - login (chave no secrets.toml)
  - senha
  - nome (exibido no header)
  - lojas (lista de lojas que pode ver)

Uso no app.py:
    import auth
    if not auth.tela_login():
        st.stop()
"""

import streamlit as st


# ============================================================
# CARREGAMENTO DOS USUÁRIOS
# ============================================================
def _carregar_usuarios():
    """Lê o bloco [usuarios] do secrets.toml."""
    try:
        return dict(st.secrets.get("usuarios", {}))
    except Exception:
        return {}


# ============================================================
# AUTENTICAÇÃO
# ============================================================
def autenticar(usuario: str, senha: str):
    """
    Verifica usuário e senha.
    Retorna o dict do usuário (com nome, lojas, etc.) ou None.
    """
    usuarios = _carregar_usuarios()
    dados = usuarios.get(usuario)

    if not dados:
        return None

    senha_correta = dados.get("senha", "")
    if not senha_correta:
        return None

    if senha == senha_correta:
        return dados

    return None


# ============================================================
# TELA DE LOGIN
# ============================================================
def tela_login():
    """
    Mostra a tela de login.
    Retorna True se o usuário já está autenticado.
    """
    if st.session_state.get("autenticado"):
        return True

    # CSS específico da tela de login
    st.markdown(
        """
        <style>
        .login-box {
            max-width: 420px;
            margin: 60px auto 20px;
            padding: 32px 36px;
            background: linear-gradient(145deg, #0D2D45, #071A29);
            border: 1px solid #124866;
            border-radius: 14px;
            box-shadow: 0 0 30px rgba(22,200,255,.10);
        }
        .login-title {
            color: #F4F8FB;
            font-size: 26px;
            font-weight: 800;
            text-align: center;
            margin: 0;
            letter-spacing: .5px;
        }
        .login-sub {
            color: #8FA6B8;
            font-size: 13px;
            text-align: center;
            margin: 6px 0 0;
        }
        </style>
        <div class="login-box">
            <div class="login-title">📊 CLAYTON GWM</div>
            <div class="login-sub">Dashboard de Lucratividade</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        usuario = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Entrar", use_container_width=True, type="primary"):
            dados = autenticar(usuario, senha)

            if dados:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["nome_usuario"] = dados.get("nome", usuario)
                st.session_state["lojas_permitidas"] = dados.get("lojas", [])
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    return False


# ============================================================
# LOGOUT
# ============================================================
def logout():
    """Limpa a sessão e volta pra tela de login."""
    for chave in ["autenticado", "usuario", "nome_usuario", "lojas_permitidas"]:
        st.session_state.pop(chave, None)
    st.rerun()


# ============================================================
# HELPERS (usados pelo app.py)
# ============================================================
def lojas_do_usuario():
    """Lojas que o usuário logado pode ver."""
    return st.session_state.get("lojas_permitidas", [])


def nome_usuario():
    """Nome amigável do usuário logado."""
    return st.session_state.get("nome_usuario", "")


def usuario_atual():
    """Login (chave) do usuário logado."""
    return st.session_state.get("usuario", "")


def esta_logado():
    """True se o usuário está autenticado."""
    return bool(st.session_state.get("autenticado"))