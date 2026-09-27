import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  BookmarkCheck,
  MessageSquare,
  Sparkles,
  Award,
} from 'lucide-react'

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/applications', label: 'Applications', icon: Users },
  { path: '/shortlist', label: 'Shortlist', icon: BookmarkCheck },
  { path: '/interviews', label: 'Discussions', icon: MessageSquare },
  { path: '/team', label: 'Team Formation', icon: Award },
]

export function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <Sparkles size={20} className="brand-icon" />
          <span className="brand-name">ARTS</span>
        </div>
        <span className="brand-tagline">Recruiter Console</span>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">WORKFLOW</div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'nav-item-active' : ''}`
              }
            >
              <Icon size={18} className="nav-icon" />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="recruiter-badge">
          <span className="role-dot" />
          <span>Team Lead / Recruiter</span>
        </div>
      </div>
    </aside>
  )
}
