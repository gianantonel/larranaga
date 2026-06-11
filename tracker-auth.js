// tracker-auth.js — Autenticación con Supabase para Optimizar Tracker

const TRACKER_SESSION_KEY = 'optimizar_tracker_session';

// ── Supabase client ───────────────────────────────────────────────────────────
let _supabase = null;

function getSupabase() {
  if (_supabase) return _supabase;
  if (typeof window.supabase === 'undefined') {
    console.error('Supabase SDK no cargado.');
    return null;
  }
  if (!window.TRACKER_CONFIG || !window.TRACKER_CONFIG.supabaseUrl || !window.TRACKER_CONFIG.supabaseKey) {
    console.error('TRACKER_CONFIG no definido. Verificar tracker-config.js');
    return null;
  }
  if (window.TRACKER_CONFIG.supabaseUrl.includes('TU-PROYECTO')) {
    console.error('Credenciales sin reemplazar en tracker-config.js');
    return null;
  }
  try {
    _supabase = window.supabase.createClient(
      window.TRACKER_CONFIG.supabaseUrl,
      window.TRACKER_CONFIG.supabaseKey
    );
    return _supabase;
  } catch (e) {
    console.error('Error creando cliente Supabase:', e);
    return null;
  }
}

// ── Sesión ────────────────────────────────────────────────────────────────────
function getTrackerSession() {
  try {
    const raw = localStorage.getItem(TRACKER_SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function setTrackerSession(data) {
  localStorage.setItem(TRACKER_SESSION_KEY, JSON.stringify(data));
}

function clearTrackerSession() {
  localStorage.removeItem(TRACKER_SESSION_KEY);
}

function trackerLogout() {
  const sb = getSupabase();
  if (sb) sb.auth.signOut();
  clearTrackerSession();
  window.location.href = 'index.html';
}

// ── Protección de rutas — SIEMPRE refresca el rol desde la DB ────────────────
async function requireTrackerAuth(allowedRoles = ['admin', 'user']) {
  const session = getTrackerSession();
  if (!session) {
    window.location.href = 'index.html';
    return null;
  }

  // Refrescar el rol desde Supabase para no depender de la sesión cacheada
  try {
    const sb = getSupabase();
    if (sb) {
      const { data: profile } = await sb
        .from('tracker_users')
        .select('role, name, avatar_color')
        .eq('id', session.userId)
        .single();

      if (profile) {
        // Actualizar la sesión local con el rol fresco
        session.role = profile.role;
        session.name = profile.name;
        session.avatarColor = profile.avatar_color || session.avatarColor;
        setTrackerSession(session);
      }
    }
  } catch (e) {
    console.warn('No se pudo refrescar el rol desde DB, usando sesión cacheada:', e);
  }

  if (!allowedRoles.includes(session.role)) {
    window.location.href = session.role === 'admin' ? 'tracker-admin.html' : 'tracker-dashboard.html';
    return null;
  }

  return session;
}

// ── Login ─────────────────────────────────────────────────────────────────────
async function trackerLogin(email, password) {
  const sb = getSupabase();
  if (!sb) return { success: false, message: 'Error de configuración. Verificar tracker-config.js' };

  try {
    const { data: authData, error: authError } = await sb.auth.signInWithPassword({ email, password });
    if (authError) return { success: false, message: 'Correo o contraseña incorrectos.' };

    // Buscar perfil — siempre leer desde DB para tener el rol actualizado
    const { data: profile, error: profileError } = await sb
      .from('tracker_users')
      .select('*')
      .eq('id', authData.user.id)
      .single();

    let finalProfile = profile;

    // Si no existe el perfil, crearlo automáticamente
    if (profileError || !profile) {
      const newProfile = {
        id: authData.user.id,
        name: authData.user.user_metadata?.name || email.split('@')[0],
        email: authData.user.email,
        role: authData.user.user_metadata?.role || 'user',
        avatar_color: '#38bdf8'
      };
      const { data: created } = await sb
        .from('tracker_users')
        .insert(newProfile)
        .select()
        .single();
      finalProfile = created || newProfile;
    }

    const session = {
      userId: authData.user.id,
      email: authData.user.email,
      name: finalProfile.name,
      role: finalProfile.role,       // rol siempre desde la DB, nunca del JWT
      avatarColor: finalProfile.avatar_color || '#38bdf8',
      loginTime: new Date().toISOString()
    };

    setTrackerSession(session);
    return { success: true, role: session.role };
  } catch (e) {
    console.error('Login error:', e);
    return { success: false, message: 'Error de red. Verificá tu conexión.' };
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = `toast${type === 'error' ? ' error' : ''}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ── Lightbox ──────────────────────────────────────────────────────────────────
function openLightbox(src) {
  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  const img = document.createElement('img');
  img.src = src;
  img.alt = 'captura';
  overlay.appendChild(img);
  overlay.onclick = () => overlay.remove();
  document.body.appendChild(overlay);
}
