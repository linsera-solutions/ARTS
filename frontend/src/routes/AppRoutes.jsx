import React from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AppLayout } from '../components/layout/AppLayout'
import { Login } from '../pages/Login'
import { Dashboard } from '../pages/Dashboard'
import { ApplicationsList } from '../pages/ApplicationsList'
import { ApplicationDetail } from '../pages/ApplicationDetail'
import { ReviewEvaluation } from '../pages/ReviewEvaluation'
import { Shortlist } from '../pages/Shortlist'
import { Interviews } from '../pages/Interviews'
import { TeamFormation } from '../pages/TeamFormation'
import { LoadingSpinner } from '../components/common/Loading'

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner message="Validating recruiter session..." />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner message="Checking authorization..." />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return children
}

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Login Route */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />

      {/* Protected Recruiter Console Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* SCR-01: Dashboard */}
        <Route index element={<Dashboard />} />

        {/* SCR-02: Applications List */}
        <Route path="applications" element={<ApplicationsList />} />

        {/* SCR-03: Application & Candidate Detail */}
        <Route path="applications/:id" element={<ApplicationDetail />} />

        {/* SCR-04: Review & Evaluation */}
        <Route path="evaluations" element={<ReviewEvaluation />} />
        <Route path="review" element={<ReviewEvaluation />} />

        {/* SCR-06: Candidate Shortlist */}
        <Route path="shortlist" element={<Shortlist />} />

        {/* SCR-07: Discussions / Interviews */}
        <Route path="interviews" element={<Interviews />} />

        {/* SCR-08: Team Formation / Composition */}
        <Route path="team" element={<TeamFormation />} />

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
