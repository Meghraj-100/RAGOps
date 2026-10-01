'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, FileText, MessageSquare, FlaskConical,
  ScrollText, Activity, Settings
} from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/documents', label: 'Documents', icon: FileText },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/evaluations', label: 'Evaluations', icon: FlaskConical },
  { href: '/queries', label: 'Queries', icon: ScrollText },
  { href: '/observability', label: 'Observability', icon: Activity },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-surface-1 border-r border-surface-4 flex flex-col z-50">
      <div className="px-4 py-5 border-b border-surface-4">
        <h1 className="text-sm font-semibold tracking-wide text-zinc-200">RAG Platform</h1>
        <p className="text-[10px] text-muted mt-0.5 font-mono">eval & observability</p>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== '/' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-[13px] transition-colors ${
                isActive
                  ? 'bg-accent/10 text-accent font-medium'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-surface-3'
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-3 border-t border-surface-4">
        <p className="text-[10px] text-muted font-mono">v1.0.0</p>
      </div>
    </aside>
  )
}
