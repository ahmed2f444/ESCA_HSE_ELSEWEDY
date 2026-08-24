import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/layout.jsx'
import { useAuth } from './hooks.jsx'

// Eagerly loaded critical auth and dashboard pages
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'

// Lazily loaded modules for optimal code-splitting and small initial bundle size
const MasterData = lazy(() => import('./pages/MasterData.jsx'))
const Departments = lazy(() => import('./pages/Departments.jsx'))
const Incidents = lazy(() => import('./pages/Incidents.jsx'))
const FireEquipment = lazy(() => import('./pages/FireEquipment.jsx'))
const Ppe = lazy(() => import('./pages/Ppe.jsx'))
const Inspections = lazy(() => import('./pages/Inspections.jsx'))
const Risk = lazy(() => import('./pages/Risk.jsx'))
const Permits = lazy(() => import('./pages/Permits.jsx'))
const Jsa = lazy(() => import('./pages/Jsa.jsx'))
const Hazmat = lazy(() => import('./pages/Hazmat.jsx'))
const OccupationalHealth = lazy(() => import('./pages/OccupationalHealth.jsx'))
const Training = lazy(() => import('./pages/Training.jsx'))
const AiIot = lazy(() => import('./pages/AiIot.jsx'))
const AiAgent = lazy(() => import('./pages/AiAgent.jsx'))
const Integrations = lazy(() => import('./pages/Integrations.jsx'))
const Security = lazy(() => import('./pages/Security.jsx'))
const Architecture = lazy(() => import('./pages/Architecture.jsx'))
const Reports = lazy(() => import('./pages/Reports.jsx'))
const NotFound = lazy(() => import('./pages/NotFound.jsx'))

function PageFallback() {
  return (
    <div className="py-24 flex flex-col items-center justify-center text-center">
      <div className="w-8 h-8 border-2 border-txt-3/20 border-t-hi rounded-full animate-spin mb-3" />
      <span className="text-xs text-txt-3 font-mono">جاري تحميل الشاشة…</span>
    </div>
  )
}

function RequireAuth({ children }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) return <Navigate to="/login" state={{ from: loc.pathname }} replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route
          path="master-data"
          element={
            <Suspense fallback={<PageFallback />}>
              <MasterData />
            </Suspense>
          }
        />
        <Route
          path="departments"
          element={
            <Suspense fallback={<PageFallback />}>
              <Departments />
            </Suspense>
          }
        />
        <Route
          path="incidents"
          element={
            <Suspense fallback={<PageFallback />}>
              <Incidents />
            </Suspense>
          }
        />
        <Route
          path="fire-equipment"
          element={
            <Suspense fallback={<PageFallback />}>
              <FireEquipment />
            </Suspense>
          }
        />
        <Route
          path="ppe"
          element={
            <Suspense fallback={<PageFallback />}>
              <Ppe />
            </Suspense>
          }
        />
        <Route
          path="inspections"
          element={
            <Suspense fallback={<PageFallback />}>
              <Inspections />
            </Suspense>
          }
        />
        <Route
          path="risk"
          element={
            <Suspense fallback={<PageFallback />}>
              <Risk />
            </Suspense>
          }
        />
        <Route
          path="permits"
          element={
            <Suspense fallback={<PageFallback />}>
              <Permits />
            </Suspense>
          }
        />
        <Route
          path="jsa"
          element={
            <Suspense fallback={<PageFallback />}>
              <Jsa />
            </Suspense>
          }
        />
        <Route
          path="hazmat"
          element={
            <Suspense fallback={<PageFallback />}>
              <Hazmat />
            </Suspense>
          }
        />
        <Route
          path="occupational-health"
          element={
            <Suspense fallback={<PageFallback />}>
              <OccupationalHealth />
            </Suspense>
          }
        />
        <Route
          path="training"
          element={
            <Suspense fallback={<PageFallback />}>
              <Training />
            </Suspense>
          }
        />
        <Route
          path="ai-iot"
          element={
            <Suspense fallback={<PageFallback />}>
              <AiIot />
            </Suspense>
          }
        />
        <Route
          path="ai-agent"
          element={
            <Suspense fallback={<PageFallback />}>
              <AiAgent />
            </Suspense>
          }
        />
        <Route
          path="integrations"
          element={
            <Suspense fallback={<PageFallback />}>
              <Integrations />
            </Suspense>
          }
        />
        <Route
          path="security"
          element={
            <Suspense fallback={<PageFallback />}>
              <Security />
            </Suspense>
          }
        />
        <Route
          path="architecture"
          element={
            <Suspense fallback={<PageFallback />}>
              <Architecture />
            </Suspense>
          }
        />
        <Route
          path="reports"
          element={
            <Suspense fallback={<PageFallback />}>
              <Reports />
            </Suspense>
          }
        />
        <Route
          path="*"
          element={
            <Suspense fallback={<PageFallback />}>
              <NotFound />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  )
}
