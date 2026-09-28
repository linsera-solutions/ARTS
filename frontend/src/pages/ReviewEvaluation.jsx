import React, { useState, useEffect, useCallback } from "react"
import { useSearchParams, useNavigate, Link } from "react-router-dom"
import { applicationsService, evaluationsService, notesService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import {
  ArrowLeft, CheckCircle2, Save, ExternalLink,
  ShieldCheck, MessageSquare, Trash2, Info, Send,
} from "lucide-react"

const QUALITATIVE_RATINGS = [
  { value: "Strong Evidence",       color: "#166534", bg: "#dcfce7" },
  { value: "Some Evidence",         color: "#1e40af", bg: "#dbeafe" },
  { value: "Limited Evidence",      color: "#854d0e", bg: "#fef9c3" },
  { value: "Insufficient Evidence", color: "#475569", bg: "#f1f5f9" },
  { value: "Not Applicable",        color: "#64748b", bg: "#f8fafc" },
]

const RECOMMENDATIONS = [
  { value: "Advance",           desc: "Strong candidate — recommend progressing to shortlist or discussion." },
  { value: "Needs Discussion",  desc: "Clarification needed before a decision can be made." },
  { value: "Waitlist",          desc: "Suitable backup candidate if primary selections fall through." },
  { value: "Reject",            desc: "Does not meet minimum role requirements based on submitted evidence." },
]

const REC_COLORS = {
  Advance:           { border: "#16a34a", bg: "#f0fdf4", text: "#166534" },
  "Needs Discussion":{ border: "#d97706", bg: "#fffbeb", text: "#92400e" },
  Waitlist:          { border: "#2563eb", bg: "#eff6ff", text: "#1e40af" },
  Reject:            { border: "#dc2626", bg: "#fef2f2", text: "#991b1b" },
}

export function ReviewEvaluation() {
  const [searchParams] = useSearchParams()
  const applicationId = searchParams.get("application_id")
  const navigate = useNavigate()
  const [loading, setLoading] = useState(Boolean(applicationId))
  const [error, setError] = useState(null)
  const [application, setApplication] = useState(null)
  const [criteria, setCriteria] = useState([])
  const [existingEvaluations, setExistingEvaluations] = useState([])
  const [notes, setNotes] = useState([])
  const [scores, setScores] = useState({})
  const [recommendation, setRecommendation] = useState("")
  const [strengths, setStrengths] = useState("")
  const [concerns, setConcerns] = useState("")
  const [overallComments, setOverallComments] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [savedStatus, setSavedStatus] = useState(null)
  const [noteText, setNoteText] = useState("")
  const [addingNote, setAddingNote] = useState(false)

  const loadData = useCallback(() => {
    if (!applicationId) return
    setLoading(true)
    setError(null)
    Promise.all([
      applicationsService.get(applicationId),
      evaluationsService.listCriteria(),
      evaluationsService.listByApplication(applicationId),
      notesService.listByEntity("Application", applicationId),
    ])
      .then(([appData, criteriaData, evalsData, notesData]) => {
        setApplication(appData)
        setCriteria(criteriaData || [])
        setExistingEvaluations(evalsData || [])
        setNotes(notesData || [])
        const draft = (evalsData || []).find((e) => e.evaluation_status === "Draft")
        const latest = draft || (evalsData || [])[0]
        if (latest) {
          if (latest.overall_recommendation) setRecommendation(latest.overall_recommendation)
          if (latest.strengths) setStrengths(latest.strengths)
          if (latest.concerns) setConcerns(latest.concerns)
          if (latest.overall_comments) setOverallComments(latest.overall_comments)
          const init = {}
          ;(latest.scores || []).forEach((sc) => {
            init[sc.criterion_id] = {
              qualitative_rating: sc.qualitative_rating || "Insufficient Evidence",
              score_comment: sc.score_comment || "",
            }
          })
          setScores(init)
        } else {
          const init = {}
          ;(criteriaData || []).forEach((c) => {
            init[c.id] = { qualitative_rating: "Insufficient Evidence", score_comment: "" }
          })
          setScores(init)
        }
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false))
  }, [applicationId])

  useEffect(() => { loadData() }, [loadData])

  const handleScoreChange = (cid, field, value) =>
    setScores((prev) => ({ ...prev, [cid]: { ...prev[cid], [field]: value } }))

  const handleSave = async (evalStatus) => {
    if (!applicationId) return
    setSubmitting(true)
    setSavedStatus(null)
    try {
      const scoresPayload = Object.entries(scores).map(([cid, d]) => ({
        criterion_id: cid,
        qualitative_rating: d.qualitative_rating,
        score_comment: d.score_comment || null,
        score_value: null,
      }))
      await evaluationsService.upsert({
        application_id: applicationId,
        overall_recommendation: recommendation || null,
        strengths: strengths || null,
        concerns: concerns || null,
        overall_comments: overallComments || null,
        evaluation_status: evalStatus,
        scores: scoresPayload,
      })
      setSavedStatus(evalStatus === "Submitted" ? "submitted" : "draft")
      await loadData()
    } catch (err) {
      alert("Failed to save evaluation: " + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!noteText.trim()) return
    setAddingNote(true)
    try {
      await notesService.create({
        author_id: application.applicant_id,
        related_entity_type: "Application",
        related_entity_id: applicationId,
        note_text: noteText.trim(),
        visibility: "Internal",
      })
      setNoteText("")
      const nd = await notesService.listByEntity("Application", applicationId)
      setNotes(nd || [])
    } catch (err) {
      alert("Failed to add note: " + err.message)
    } finally {
      setAddingNote(false)
    }
  }

  const handleDeleteNote = async (nid) => {
    if (!window.confirm("Delete this note?")) return
    try {
      await notesService.delete(nid)
      setNotes((prev) => prev.filter((n) => n.id !== nid))
    } catch (err) {
      alert("Failed to delete note: " + err.message)
    }
  }

  if (loading) return <LoadingSpinner message="Loading candidate review workspace..." />
  if (error) return <ErrorAlert error={error} />
  if (!application) {
    return (
      <div className="page-container">
        <Card>
          <p style={{ color: "#64748b" }}>No application selected.</p>
          <Link to="/applications" className="btn btn-primary btn-sm" style={{ marginTop: "1rem" }}>
            Go to Applications List
          </Link>
        </Card>
      </div>
    )
  }

  const applicant = application.applicant || {}
  const role = application.role || {}

  return (
    <div className="page-container">
      <div style={{ marginBottom: "1rem" }}>
        <button type="button" onClick={() => navigate(-1)} className="btn btn-outline btn-sm"
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <ArrowLeft size={16} /><span>Back</span>
        </button>
      </div>

      {/* Decision-Support Notice */}
      <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "8px",
        padding: "1rem 1.25rem", marginBottom: "1.5rem", display: "flex", alignItems: "flex-start", gap: "0.85rem" }}>
        <ShieldCheck size={22} style={{ color: "#2563eb", flexShrink: 0, marginTop: "2px" }} />
        <div>
          <strong style={{ color: "#1e40af", fontSize: "0.93rem" }}>Decision-Support Mode — Human Review Required</strong>
          <p style={{ margin: "0.25rem 0 0 0", color: "#1e3a8a", fontSize: "0.82rem", lineHeight: "1.55" }}>
            ARTS does not automatically score, rank, or select candidates. Evaluations record the
            strength of <em>submitted evidence</em> across qualitative dimensions. Missing evidence
            should be marked <strong>Insufficient Evidence</strong> — not treated as automatic failure.
            All selection decisions remain with the Team Lead.
          </p>
        </div>
      </div>

      {/* Candidate Header */}
      <Card style={{ backgroundColor: "#f8fafc", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <h1 style={{ fontSize: "1.35rem", margin: 0, color: "#0f172a" }}>{applicant.full_name || "Candidate"}</h1>
              <Badge>{application.current_status}</Badge>
            </div>
            <p style={{ margin: "0.35rem 0 0 0", color: "#475569", fontSize: "0.92rem" }}>
              Applied for: <strong>{role.role_name}</strong> &bull; {applicant.email}
              {applicant.location && <> &bull; {applicant.location}</>}
            </p>
          </div>
          <Link to={`/applications/${applicationId}`} className="btn btn-outline btn-sm">Full Profile</Link>
        </div>
      </Card>

      {savedStatus && (
        <div style={{ backgroundColor: savedStatus === "submitted" ? "#f0fdf4" : "#fefce8",
          border: `1px solid ${savedStatus === "submitted" ? "#86efac" : "#fde047"}`,
          borderRadius: "8px", padding: "0.75rem 1rem", marginBottom: "1.25rem",
          display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <CheckCircle2 size={18} color={savedStatus === "submitted" ? "#16a34a" : "#ca8a04"} />
          <span style={{ fontSize: "0.88rem", fontWeight: "600",
            color: savedStatus === "submitted" ? "#166534" : "#92400e" }}>
            {savedStatus === "submitted"
              ? "Evaluation submitted — part of the candidate review record."
              : "Draft saved. Continue editing and submit when ready."}
          </span>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.35fr", gap: "1.5rem", alignItems: "start" }}>
        {/* LEFT: Submitted Evidence */}
        <div>
          <Card title="Submitted Evidence" style={{ marginBottom: "1.25rem" }}>
            <div style={{ backgroundColor: "#fef9c3", border: "1px solid #fde047", borderRadius: "6px",
              padding: "0.5rem 0.75rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Info size={14} color="#854d0e" />
              <span style={{ fontSize: "0.78rem", color: "#854d0e" }}>
                Content below is submitted by the applicant. Do not modify during review.
              </span>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                Motivation Statement
              </div>
              <p style={{ margin: 0, color: "#1e293b", fontSize: "0.88rem", lineHeight: "1.6" }}>
                {application.motivation_statement || <em style={{ color: "#94a3b8" }}>No statement provided.</em>}
              </p>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.3rem" }}>
                Availability
              </div>
              <p style={{ margin: 0, color: "#1e293b", fontSize: "0.88rem" }}>
                {application.availability_info || <em style={{ color: "#94a3b8" }}>Not specified.</em>}
              </p>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.35rem" }}>
                Claimed Skills ({applicant.applicant_skills?.length || 0})
              </div>
              {applicant.applicant_skills?.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                  {applicant.applicant_skills.map((s) => (
                    <span key={s.id} style={{ backgroundColor: "#e2e8f0", color: "#334155",
                      padding: "0.2rem 0.55rem", borderRadius: "9999px", fontSize: "0.78rem" }}>
                      {s.skill?.skill_name}{s.proficiency_level && ` (${s.proficiency_level})`}
                    </span>
                  ))}
                </div>
              ) : <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.82rem" }}>No skills claimed.</p>}
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.35rem" }}>
                Evidence Links ({applicant.portfolio_items?.length || 0})
              </div>
              {applicant.portfolio_items?.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                  {applicant.portfolio_items.map((item) => (
                    <div key={item.id} style={{ padding: "0.5rem 0.7rem", backgroundColor: "#f8fafc",
                      border: "1px solid #e2e8f0", borderRadius: "6px" }}>
                      <div style={{ fontWeight: "600", fontSize: "0.82rem", color: "#0f172a" }}>{item.title}</div>
                      {item.reference_link && (
                        <a href={item.reference_link} target="_blank" rel="noreferrer"
                          style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem",
                            color: "#2563eb", fontSize: "0.77rem", marginTop: "0.15rem", wordBreak: "break-all" }}>
                          <ExternalLink size={11} />{item.reference_link}
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ) : <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.82rem" }}>No evidence links submitted.</p>}
            </div>

            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.35rem" }}>
                Work / Project Experience ({applicant.experiences?.length || 0})
              </div>
              {applicant.experiences?.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                  {applicant.experiences.map((exp) => (
                    <div key={exp.id} style={{ padding: "0.5rem 0.7rem", backgroundColor: "#f8fafc",
                      border: "1px solid #e2e8f0", borderRadius: "6px" }}>
                      <strong style={{ fontSize: "0.82rem", color: "#0f172a" }}>{exp.title}</strong>
                      {exp.organization && <div style={{ fontSize: "0.77rem", color: "#64748b" }}>{exp.organization}</div>}
                      {exp.description && <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.77rem", color: "#334155" }}>{exp.description}</p>}
                    </div>
                  ))}
                </div>
              ) : <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.82rem" }}>No experience listed.</p>}
            </div>
          </Card>

          {/* Reviewer Notes */}
          <Card title="Reviewer Notes">
            <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.78rem", color: "#64748b" }}>
              Informal annotations — separate from the formal evaluation. Internal, not visible to applicants.
            </p>
            <form onSubmit={handleAddNote} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <input type="text" className="form-control" style={{ fontSize: "0.85rem", flex: 1 }}
                placeholder="Add a quick observation or question..."
                value={noteText} onChange={(e) => setNoteText(e.target.value)} disabled={addingNote} />
              <button type="submit" className="btn btn-primary btn-sm" disabled={addingNote || !noteText.trim()}>
                <Send size={14} />
              </button>
            </form>
            {notes.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                {notes.map((note) => (
                  <div key={note.id} style={{ padding: "0.5rem 0.7rem", backgroundColor: "#f8fafc",
                    border: "1px solid #e2e8f0", borderRadius: "6px",
                    display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                    <div>
                      <p style={{ margin: 0, fontSize: "0.83rem", color: "#1e293b" }}>{note.note_text}</p>
                      <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                        {new Date(note.created_at).toLocaleString()}
                      </span>
                    </div>
                    <button onClick={() => handleDeleteNote(note.id)}
                      style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", flexShrink: 0 }}>
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            ) : <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.82rem" }}>No notes yet.</p>}
          </Card>
        </div>

        {/* RIGHT: Reviewer Assessment Form */}
        <div>
          <Card title="Reviewer Assessment">
            <div style={{ backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "6px",
              padding: "0.5rem 0.75rem", marginBottom: "1.25rem",
              display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <MessageSquare size={14} color="#16a34a" />
              <span style={{ fontSize: "0.78rem", color: "#166534" }}>
                All fields below are <strong>reviewer-authored</strong> — distinct from applicant-submitted content.
              </span>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSave("Submitted") }}>
              {/* Per-Criterion Ratings */}
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#374151", marginBottom: "0.5rem",
                textTransform: "uppercase", letterSpacing: "0.05em" }}>Evidence Strength Assessment</h3>
              <p style={{ margin: "0 0 1rem 0", fontSize: "0.78rem", color: "#64748b" }}>
                For each criterion, select the strength of evidence in the submission.
                Criteria without supporting evidence should be marked <em>Insufficient Evidence</em>.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "1.5rem" }}>
                {criteria.map((crit, idx) => {
                  const sc = scores[crit.id] || { qualitative_rating: "Insufficient Evidence", score_comment: "" }
                  return (
                    <div key={crit.id} style={{ border: "1px solid #e2e8f0", borderRadius: "8px",
                      padding: "0.9rem 1rem", backgroundColor: "#ffffff" }}>
                      <div style={{ marginBottom: "0.6rem" }}>
                        <strong style={{ fontSize: "0.88rem", color: "#0f172a" }}>{idx + 1}. {crit.criterion_name}</strong>
                        {crit.criterion_description && (
                          <p style={{ margin: "0.15rem 0 0 0", fontSize: "0.76rem", color: "#64748b", lineHeight: "1.45" }}>
                            {crit.criterion_description}
                          </p>
                        )}
                      </div>
                      <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap", marginBottom: "0.5rem" }}>
                        {QUALITATIVE_RATINGS.map((q) => {
                          const sel = sc.qualitative_rating === q.value
                          return (
                            <button key={q.value} type="button"
                              onClick={() => handleScoreChange(crit.id, "qualitative_rating", q.value)}
                              style={{ padding: "0.25rem 0.6rem", borderRadius: "9999px", fontSize: "0.74rem",
                                fontWeight: sel ? "700" : "400", cursor: "pointer",
                                border: sel ? `2px solid ${q.color}` : "1px solid #cbd5e1",
                                backgroundColor: sel ? q.bg : "#f8fafc",
                                color: sel ? q.color : "#64748b" }}>
                              {q.value}
                            </button>
                          )
                        })}
                      </div>
                      <textarea value={sc.score_comment}
                        onChange={(e) => handleScoreChange(crit.id, "score_comment", e.target.value)}
                        placeholder={`Note evidence observed, or reason for assessment...`}
                        rows={2} className="form-control" style={{ fontSize: "0.82rem" }} />
                    </div>
                  )
                })}
              </div>

              {/* Strengths & Concerns */}
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#374151", marginBottom: "0.75rem",
                textTransform: "uppercase", letterSpacing: "0.05em" }}>Reviewer Observations</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.25rem" }}>
                <div className="form-group">
                  <label className="form-label" style={{ color: "#166534", fontWeight: "600" }}>Key Strengths Observed</label>
                  <textarea value={strengths} onChange={(e) => setStrengths(e.target.value)}
                    placeholder="Evidence-backed strengths relevant to this role..." rows={3}
                    className="form-control" style={{ fontSize: "0.83rem" }} />
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ color: "#991b1b", fontWeight: "600" }}>Concerns / Open Questions</label>
                  <textarea value={concerns} onChange={(e) => setConcerns(e.target.value)}
                    placeholder="Items to verify, ambiguities, or gaps..." rows={3}
                    className="form-control" style={{ fontSize: "0.83rem" }} />
                </div>
              </div>

              {/* Recommendation */}
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#374151", marginBottom: "0.4rem",
                textTransform: "uppercase", letterSpacing: "0.05em" }}>Overall Recommendation</h3>
              <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.78rem", color: "#64748b" }}>
                Your professional recommendation — set by you, never by ARTS automatically.
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "1.25rem" }}>
                {RECOMMENDATIONS.map((rec) => {
                  const colors = REC_COLORS[rec.value]
                  const sel = recommendation === rec.value
                  return (
                    <label key={rec.value} style={{ display: "flex", flexDirection: "column", gap: "0.25rem",
                      padding: "0.65rem 0.85rem",
                      border: sel ? `2px solid ${colors.border}` : "1px solid #cbd5e1",
                      borderRadius: "8px", backgroundColor: sel ? colors.bg : "#ffffff", cursor: "pointer" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <input type="radio" name="recommendation" value={rec.value}
                          checked={sel} onChange={(e) => setRecommendation(e.target.value)} />
                        <span style={{ fontWeight: "600", fontSize: "0.85rem", color: sel ? colors.text : "#374151" }}>
                          {rec.value}
                        </span>
                      </div>
                      <span style={{ fontSize: "0.75rem", color: "#64748b", marginLeft: "1.4rem" }}>{rec.desc}</span>
                    </label>
                  )
                })}
              </div>

              {/* Overall Comments */}
              <div className="form-group" style={{ marginBottom: "1.5rem" }}>
                <label className="form-label">Reviewer Rationale & Holistic Synthesis</label>
                <p style={{ margin: "0 0 0.4rem 0", fontSize: "0.78rem", color: "#64748b" }}>
                  Summarise your overall assessment. Required before submitting.
                </p>
                <textarea value={overallComments} onChange={(e) => setOverallComments(e.target.value)}
                  placeholder="Holistic qualitative synthesis supporting your recommendation..."
                  rows={4} className="form-control" />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                <Button type="button" variant="outline" icon={Save}
                  onClick={() => handleSave("Draft")} disabled={submitting}>
                  Save as Draft
                </Button>
                <Button type="submit" variant="primary" loading={submitting} icon={CheckCircle2}>
                  Submit Final Evaluation
                </Button>
              </div>
            </form>
          </Card>

          {/* Evaluation History */}
          {existingEvaluations.length > 0 && (
            <Card title="Evaluation History" style={{ marginTop: "1.25rem" }}>
              <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.78rem", color: "#64748b" }}>
                Recorded evaluations for this application. Submitted evaluations are preserved for auditability.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem" }}>
                {existingEvaluations.map((ev) => (
                  <div key={ev.id} style={{ padding: "0.9rem 1rem", border: "1px solid #e2e8f0",
                    borderRadius: "8px", backgroundColor: "#f8fafc" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        {ev.overall_recommendation && (
                          <span style={{ padding: "0.2rem 0.6rem", borderRadius: "9999px", fontSize: "0.78rem",
                            fontWeight: "600",
                            backgroundColor: REC_COLORS[ev.overall_recommendation]?.bg || "#f1f5f9",
                            color: REC_COLORS[ev.overall_recommendation]?.text || "#475569",
                            border: `1px solid ${REC_COLORS[ev.overall_recommendation]?.border || "#cbd5e1"}` }}>
                            {ev.overall_recommendation}
                          </span>
                        )}
                        <Badge>{ev.evaluation_status}</Badge>
                      </div>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                        {new Date(ev.updated_at || ev.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {ev.strengths && (
                      <div style={{ fontSize: "0.82rem", marginBottom: "0.25rem" }}>
                        <strong style={{ color: "#166534" }}>Strengths: </strong>
                        <span style={{ color: "#334155" }}>{ev.strengths}</span>
                      </div>
                    )}
                    {ev.concerns && (
                      <div style={{ fontSize: "0.82rem", marginBottom: "0.25rem" }}>
                        <strong style={{ color: "#991b1b" }}>Concerns: </strong>
                        <span style={{ color: "#334155" }}>{ev.concerns}</span>
                      </div>
                    )}
                    {ev.overall_comments && (
                      <p style={{ margin: "0.4rem 0 0 0", fontSize: "0.82rem", color: "#1e293b" }}>
                        {ev.overall_comments}
                      </p>
                    )}
                    {ev.scores?.length > 0 && (
                      <div style={{ marginTop: "0.6rem", paddingTop: "0.6rem", borderTop: "1px solid #e2e8f0" }}>
                        <div style={{ fontSize: "0.72rem", fontWeight: "700", color: "#64748b",
                          textTransform: "uppercase", marginBottom: "0.35rem" }}>Criterion Assessments:</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                          {ev.scores.map((sc) => {
                            const rc = QUALITATIVE_RATINGS.find((r) => r.value === sc.qualitative_rating)
                            return (
                              <span key={sc.id} title={sc.score_comment || undefined}
                                style={{ fontSize: "0.72rem", padding: "0.18rem 0.48rem", borderRadius: "4px",
                                  backgroundColor: rc?.bg || "#f1f5f9",
                                  color: rc?.color || "#475569" }}>
                                {sc.criterion?.criterion_name || "Criterion"}: {sc.qualitative_rating || "—"}
                              </span>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
