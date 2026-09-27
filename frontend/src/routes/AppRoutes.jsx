import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { Dashboard } from '../pages/Dashboard'
import { ApplicationsList } from '../pages/ApplicationsList'
import { ApplicationDetail } from '../pages/ApplicationDetail'
import { ReviewEvaluation } from '../pages/ReviewEvaluation'
import { Shortlist } from '../pages/Shortlist'
import { Interviews } from '../pages/Interviews'
import { TeamFormation } from '../pages/TeamFormation'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        {/* SCR-01: Dashboard */}
        <Route index element={<Dashboard />} />

        {/* SCR-02: Applications List */}
        <Route path="applications" element={<ApplicationsList />} />

        {/* SCR-03: Application & Candidate Detail */}
        <Route path="applications/:id" element={<ApplicationDetail />} />

        {/* SCR-04: Review & Evaluation */}
        <Route path="evaluations" element={<ReviewEvaluation />} />

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
