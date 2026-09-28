import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { rolesService, applicationsService, teamsService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import {
  Users,
  BookmarkCheck,
  Award,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Calendar,
  MessageSquare,
} from "lucide-react"

export function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [roles, setRoles] = useState([])
  const [applications, setApplications] = useState([])
  const [teamOverview, setTeamOverview] = useState(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [rolesData, appsData, teamData] = await Promise.all([
        rolesService.list(),
        applicationsService.list({ page_size: 100 }),
        teamsService.getOverview().catch(() => null),
      ])
      setRoles(rolesData?.items || rolesData || [])
      setApplications(appsData?.items || appsData || [])
      setTeamOverview(teamData)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return <LoadingSpinner message="Loading recruitment overview..." />
  }

  if (error) {
    return <ErrorAlert error={error} onRetry={loadData} />
  }

  const counts = {
    total: applications.length,
    received: applications.filter((a) => a.current_status === "Received").length,
    underReview: applications.filter((a) => a.current_status === "Under Review").length,
    shortlisted: applications.filter((a) => a.current_status === "Shortlisted").length,
    interviews: applications.filter((a) => a.current_status === "Discussion / Interview").length,
    selected: applications.filter((a) => a.current_status === "Selected").length,
  }

  const filledCount = teamOverview?.filled_slots_count ?? counts.selected

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Recruitment Dashboard</h1>
          <p className="page-subtitle">
            Applicant Review & Team Selection Overview for NASA Space Apps Challenge
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Link to="/team">
            <Button variant="outline" icon={Award}>
              Team Roster ({filledCount}/4)
            </Button>
          </Link>
          <Link to="/applications">
            <Button icon={ArrowRight}>View All Applications</Button>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Total Applications</span>
            <Users size={18} className="text-blue-500" />
          </div>
          <div className="metric-value">{counts.total}</div>
          <span className="metric-meta">From Google Forms intake</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">In Review / Screening</span>
            <Sparkles size={18} className="text-amber-500" />
          </div>
          <div className="metric-value">{counts.underReview + counts.received}</div>
          <span className="metric-meta">{counts.received} awaiting initial screening</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Shortlisted & Discussion</span>
            <BookmarkCheck size={18} className="text-indigo-500" />
          </div>
          <div className="metric-value">{counts.shortlisted + counts.interviews}</div>
          <span className="metric-meta">{counts.interviews} active in discussions</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Team Confirmed</span>
            <Award size={18} className="text-emerald-500" />
          </div>
          <div className="metric-value">{filledCount} / 4</div>
          <span className="metric-meta">Approved roster positions</span>
        </div>
      </div>

      {/* Roles Progress Grid */}
      <div style={{ marginTop: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 className="section-title" style={{ margin: 0 }}>
            Target Team Roles (4 Positions)
          </h2>
          <Link to="/team" style={{ fontSize: "0.85rem", color: "#2563eb", textDecoration: "none" }}>
            Assemble Team Roster &rarr;
          </Link>
        </div>

        <div className="roles-overview-grid">
          {roles.map((role) => {
            const roleApps = applications.filter((a) => a.role_id === role.id)
            const roleShortlisted = roleApps.filter((a) => a.current_status === "Shortlisted").length
            const roleInterview = roleApps.filter((a) => a.current_status === "Discussion / Interview").length
            const isFilled = teamOverview?.slots?.find((s) => s.role_id === role.id)?.is_filled ?? false

            return (
              <Card
                key={role.id}
                title={role.role_name}
                subtitle={`1 opening • ${roleApps.length} applicant(s)`}
                action={
                  <Badge variant={isFilled ? "Selected" : "Open"}>
                    {isFilled ? "Slot Filled" : "Position Open"}
                  </Badge>
                }
              >
                <p className="role-card-description">{role.role_description}</p>
                <div className="role-stats-footer">
                  <div className="stat-pill">
                    <strong>{roleShortlisted + roleInterview}</strong> in consideration
                  </div>
                  <Link to={`/applications?role=${role.id}`} className="link-action">
                    Review Candidates &rarr;
                  </Link>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}