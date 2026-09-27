import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { applicationsService, notesService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Modal } from '../components/common/Modal'
import {
  User,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  Clock,
  FileText,
  Briefcase,
  Layers,
  Sparkles,
  MessageSquare,
  ArrowLeft,
  Calendar,
  History,
} from 'lucide-react'

const APPROVED_STATUSES = [
  'Received',
  'Under Review',
  'Shortlisted',
  'Discussion / Interview',
  'Selected',
  'Not Selected',
  'Withdrawn',
]

export function ApplicationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [application, setApplication] = useState(null)
  const [notes, setNotes] = useState([])

  // Status update modal
  const [statusModalOpen, setStatusModalOpen] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [statusReason, setStatusReason] = useState('')
  const [updatingStatus, setUpdatingStatus] = useState(false)

  // Note creation state
  const [newNoteText, setNewNoteText] = useState('')
  const [addingNote, setAddingNote] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [appData, notesData] = await Promise.all([
        applicationsService.get(id),
        notesService.listByEntity('Application', id),
      ])
      setApplication(appData)
      setNotes(notesData || [])
      setNewStatus(appData?.current_status || '')
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [id])

  const handleStatusSubmit = async (e) => {
    e.preventDefault()
    setUpdatingStatus(true)
    try {
      await applicationsService.updateStatus(id, {
        new_status: newStatus,
        reason: statusReason || 'Status update via application detail view',
      })
      setStatusModalOpen(false)
      setStatusReason('')
      loadData()
    } catch (err) {
      alert(`Failed to update status: ${err.message}`)
    } finally {
      setUpdatingStatus(false)
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!newNoteText.trim()) return

    setAddingNote(true)
    try {
      // For MVP foundation, notes take an author ID or system author
      await notesService.create({
        author_id: application.applicant_id, // Author ID fallback
        related_entity_type: 'Application',
        related_entity_id: id,
        note_text: newNoteText,
        visibility: 'Internal',
      })
      setNewNoteText('')
      const updatedNotes = await notesService.listByEntity('Application', id)
      setNotes(updatedNotes || [])
    } catch (err) {
      alert(`Failed to add note: ${err.message}`)
    } finally {
      setAddingNote(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading candidate profile..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />
  if (!application) return <ErrorAlert message="Application not found." />

  const applicant = application.applicant || {}
  const role = application.role || {}

  return (
    <div className="page-container">
      <div style={{ marginBottom: '1rem' }}>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="btn btn-outline btn-sm"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <ArrowLeft size={16} />
          <span>Back to Applications</span>
        </button>
      </div>

      {/* Candidate Profile Header Card */}
      <div className="profile-header-card">
        <div className="profile-header-top">
          <div className="profile-identity">
            <div className="profile-avatar">
              <User size={32} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <h1 className="profile-name">{applicant.full_name || 'Candidate Name'}</h1>
                <Badge>{application.current_status}</Badge>
              </div>
              <p className="profile-applied-role">
                Applied for: <strong>{role.role_name}</strong>
              </p>
            </div>
          </div>

          <div className="profile-header-actions">
            <Button
              variant="outline"
              onClick={() => setStatusModalOpen(true)}
            >
              Update Status
            </Button>
            <Link to={`/evaluations?application_id=${id}`}>
              <Button icon={Sparkles}>
                Record Evaluation
              </Button>
            </Link>
          </div>
        </div>

        {/* Contact info bar */}
        <div className="profile-contact-bar">
          <div className="contact-item">
            <Mail size={15} />
            <span>{applicant.email}</span>
          </div>
          {applicant.phone_number && (
            <div className="contact-item">
              <Phone size={15} />
              <span>{applicant.phone_number}</span>
            </div>
          )}
          {applicant.location && (
            <div className="contact-item">
              <MapPin size={15} />
              <span>{applicant.location}</span>
            </div>
          )}
          {applicant.external_profile_link && (
            <div className="contact-item">
              <ExternalLink size={15} />
              <a
                href={applicant.external_profile_link}
                target="_blank"
                rel="noreferrer"
                className="external-link"
              >
                External Portfolio / LinkedIn
              </a>
            </div>
          )}
        </div>
      </div>

      {/* 2-Column Detail Layout */}
      <div className="detail-grid">
        {/* Left Column: Evidence, Motivation, Experiences, Portfolio */}
        <div className="detail-column-main">
          {/* Motivation & Availability */}
          <Card title="Motivation & Availability" className="mb-4">
            <div style={{ marginBottom: '1.25rem' }}>
              <strong className="field-title">Motivation Statement</strong>
              <p className="field-content">
                {application.motivation_statement || 'No statement submitted.'}
              </p>
            </div>
            {application.availability_info && (
              <div>
                <strong className="field-title">Availability / Constraints</strong>
                <p className="field-content">{application.availability_info}</p>
              </div>
            )}
          </Card>

          {/* Submitted Portfolio & Evidence Links */}
          <Card title="Submitted Evidence & Portfolio Items" className="mb-4">
            {applicant.portfolio_items && applicant.portfolio_items.length > 0 ? (
              <div className="evidence-list">
                {applicant.portfolio_items.map((item) => (
                  <div key={item.id} className="evidence-item">
                    <div className="evidence-header">
                      <FileText size={18} className="text-indigo-500" />
                      <strong>{item.title}</strong>
                    </div>
                    {item.description && (
                      <p className="evidence-desc">{item.description}</p>
                    )}
                    {item.reference_link && (
                      <a
                        href={item.reference_link}
                        target="_blank"
                        rel="noreferrer"
                        className="evidence-url"
                      >
                        <ExternalLink size={14} />
                        <span>{item.reference_link}</span>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No portfolio evidence attached.</p>
            )}
          </Card>

          {/* Work / Project Experiences */}
          <Card title="Prior Work & Project Experience" className="mb-4">
            {applicant.experiences && applicant.experiences.length > 0 ? (
              <div className="experience-timeline">
                {applicant.experiences.map((exp) => (
                  <div key={exp.id} className="experience-item">
                    <div className="exp-dot" />
                    <div className="exp-content">
                      <h4 className="exp-title">{exp.title}</h4>
                      <p className="exp-org">{exp.organization || 'Independent Project'}</p>
                      <span className="exp-dates">
                        {exp.start_date} &rarr; {exp.end_date || 'Present'}
                      </span>
                      {exp.description && <p className="exp-desc">{exp.description}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No prior experience records listed.</p>
            )}
          </Card>
        </div>

        {/* Right Column: Status Timeline & Reviewer Notes */}
        <div className="detail-column-side">
          {/* Claimed Skills */}
          <Card title="Claimed Skills" className="mb-4">
            {applicant.applicant_skills && applicant.applicant_skills.length > 0 ? (
              <div className="skills-pill-cloud">
                {applicant.applicant_skills.map((s) => (
                  <div key={s.id} className="skill-pill">
                    <strong>{s.skill?.skill_name || 'Skill'}</strong>
                    {s.proficiency_level && <span>({s.proficiency_level})</span>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No explicit skills listed.</p>
            )}
          </Card>

          {/* Status Audit History Timeline */}
          <Card title="Status History (Auditability)" className="mb-4">
            {application.status_history && application.status_history.length > 0 ? (
              <div className="status-history-list">
                {application.status_history.map((hist) => (
                  <div key={hist.id} className="history-step">
                    <div className="history-dot" />
                    <div>
                      <Badge>{hist.new_status}</Badge>
                      <span className="history-time">
                        {new Date(hist.changed_at).toLocaleString()}
                      </span>
                      {hist.reason && <p className="history-reason">{hist.reason}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No status transitions recorded.</p>
            )}
          </Card>

          {/* Reviewer Notes Section */}
          <Card title="Reviewer Notes" className="mb-4">
            <form onSubmit={handleAddNote} className="add-note-form">
              <textarea
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                placeholder="Add an internal reviewer note or observation..."
                rows={3}
                className="form-control"
              />
              <div style={{ marginTop: '0.5rem', textAlign: 'right' }}>
                <Button
                  type="submit"
                  size="sm"
                  variant="secondary"
                  disabled={!newNoteText.trim()}
                  loading={addingNote}
                >
                  Post Note
                </Button>
              </div>
            </form>

            <div className="notes-stream">
              {notes.map((note) => (
                <div key={note.id} className="note-card">
                  <p className="note-body">{note.note_text}</p>
                  <span className="note-meta">
                    {new Date(note.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Status Modal */}
      <Modal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title="Transition Application Status"
        footer={
          <>
            <Button variant="outline" onClick={() => setStatusModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStatusSubmit}
              loading={updatingStatus}
            >
              Update Status
            </Button>
          </>
        }
      >
        <form onSubmit={handleStatusSubmit}>
          <div className="form-group">
            <label className="form-label">Select New Lifecycle Status</label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="form-control"
              required
            >
              {APPROVED_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ marginTop: '1rem' }}>
            <label className="form-label">Decision Note / Audit Reason</label>
            <textarea
              value={statusReason}
              onChange={(e) => setStatusReason(e.target.value)}
              placeholder="State the rationale for advancing or adjusting candidate status..."
              rows={3}
              className="form-control"
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  )
}
