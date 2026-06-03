import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { FeatureFlagsProvider } from './context/FeatureFlagsContext'
import FeatureGate from './components/FeatureGate'
import Layout from './components/Layout/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Clients from './pages/Clients'
import ClientDetail from './pages/ClientDetail'
import Collaborators from './pages/Collaborators'
import Tasks from './pages/Tasks'
import IVA from './pages/IVA'
import Facturas from './pages/Facturas'
import Usuarios from './pages/Usuarios'

import Retenciones from './pages/Retenciones'
import Herramientas from './pages/Herramientas'
import CuentasCorrientes from './pages/CuentasCorrientes'
import Honorarios from './pages/Honorarios'
import Profesionales from './pages/Profesionales'
import RegistrarCobro from './pages/RegistrarCobro'
import RetirosSocios from './pages/RetirosSocios'
import FlujoDeFondos from './pages/FlujoDeFondos'
import ActualizarHonorarios from './pages/ActualizarHonorarios'
import Liquidaciones from './pages/Liquidaciones'
import PosicionIVA from './pages/PosicionIVA'
import MaestroProveedores from './pages/MaestroProveedores'
import ConciliacionBancaria from './pages/ConciliacionBancaria'
import GestionRequisitos from './pages/GestionRequisitos'
import LoadingSpinner from './components/UI/LoadingSpinner'

const Gated = ({ codigo, children }) => (
  <FeatureGate codigo={codigo} fallback={<Navigate to="/dashboard" replace />}>
    {children}
  </FeatureGate>
)

function ProtectedRoutes() {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center surface"><LoadingSpinner /></div>
  if (!user) return <Navigate to="/login" replace />
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        {/* Always visible */}
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="clientes" element={<Clients />} />
        <Route path="clientes/:id" element={<ClientDetail />} />
        <Route path="colaboradores" element={<Collaborators />} />
        <Route path="tareas" element={<Tasks />} />
        <Route path="usuarios" element={<Usuarios />} />
        <Route path="facturas" element={<Facturas />} />
        <Route path="gestion-requisitos" element={<GestionRequisitos />} />

        {/* Gated por R-XX */}
        <Route path="herramientas" element={<Gated codigo={['R-01', 'R-02']}><Herramientas /></Gated>} />
        <Route path="honorarios" element={<Gated codigo="R-03"><Honorarios /></Gated>} />
        <Route path="profesionales" element={<Gated codigo="R-04"><Profesionales /></Gated>} />
        <Route path="liquidaciones" element={<Gated codigo="R-04"><Liquidaciones /></Gated>} />
        <Route path="retenciones" element={<Gated codigo="R-05"><Retenciones /></Gated>} />
        <Route path="cuentas-corrientes" element={<Gated codigo="R-07"><CuentasCorrientes /></Gated>} />
        <Route path="iva" element={<Gated codigo="R-06"><IVA /></Gated>} />
        <Route path="posicion-iva" element={<Gated codigo="R-06"><PosicionIVA /></Gated>} />
        <Route path="cobros" element={<Gated codigo="R-08"><RegistrarCobro /></Gated>} />
        <Route path="maestro-proveedores" element={<Gated codigo="R-09"><MaestroProveedores /></Gated>} />
        <Route path="flujo-fondos" element={<Gated codigo="R-11"><FlujoDeFondos /></Gated>} />
        <Route path="retiros" element={<Gated codigo="R-12"><RetirosSocios /></Gated>} />
        <Route path="actualizar-honorarios" element={<Gated codigo="R-13"><ActualizarHonorarios /></Gated>} />
        <Route path="conciliacion-bancaria" element={<Gated codigo="R-15"><ConciliacionBancaria /></Gated>} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <FeatureFlagsProvider>
          <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
              <Route path="/register" element={<Register />} />
              <Route path="/*" element={<ProtectedRoutes />} />
            </Routes>
          </BrowserRouter>
        </FeatureFlagsProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}
