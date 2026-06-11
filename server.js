const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 80;

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://ikkmyhzmxgdbqfiwnqec.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || '';

app.use(express.json());
app.use(express.static(path.join(__dirname, '')));

// ── Crear usuario (requiere SUPABASE_SERVICE_KEY en variables de entorno) ────
app.post('/api/tracker/create-user', async (req, res) => {
  const { name, email, password, role } = req.body;
  if (!name || !email || !password) {
    return res.status(400).json({ success: false, message: 'Faltan campos requeridos.' });
  }
  if (!SUPABASE_SERVICE_KEY) {
    return res.status(500).json({
      success: false,
      message: 'Variable SUPABASE_SERVICE_KEY no configurada en el servidor. Agregarla en EasyPanel → Variables de entorno.'
    });
  }

  try {
    // 1. Crear en Supabase Auth
    const authRes = await fetch(`${SUPABASE_URL}/auth/v1/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      },
      body: JSON.stringify({
        email,
        password,
        email_confirm: true,
        user_metadata: { name, role }
      })
    });
    const authData = await authRes.json();
    if (!authRes.ok) {
      return res.status(400).json({ success: false, message: authData.message || authData.msg || 'Error creando usuario.' });
    }

    // 2. Insertar perfil en tracker_users
    const colors = ['#38bdf8', '#f472b6', '#a78bfa', '#34d399', '#fbbf24'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    const profileRes = await fetch(`${SUPABASE_URL}/rest/v1/tracker_users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify({ id: authData.id, name, email, role: role || 'user', avatar_color: randomColor })
    });
    if (!profileRes.ok) {
      console.error('Error insertando perfil:', await profileRes.text());
    }

    return res.json({ success: true, userId: authData.id });
  } catch (e) {
    console.error('Error en create-user:', e);
    return res.status(500).json({ success: false, message: 'Error interno del servidor.' });
  }
});

// ── Eliminar usuario ─────────────────────────────────────────────────────────
app.delete('/api/tracker/delete-user/:id', async (req, res) => {
  const { id } = req.params;
  if (!SUPABASE_SERVICE_KEY) {
    return res.status(500).json({ success: false, message: 'SUPABASE_SERVICE_KEY no configurada.' });
  }
  try {
    await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${id}`, {
      method: 'DELETE',
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });
    return res.json({ success: true });
  } catch (e) {
    console.error('Error en delete-user:', e);
    return res.status(500).json({ success: false, message: 'Error eliminando usuario.' });
  }
});

// Fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Optimizar Tracker running on port ${PORT}`);
});
