import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Home' },
  { to: '/translator', label: 'Translator' },
  { to: '/speech', label: 'Speech Translator' },
  { to: '/image', label: 'Image Translator' },
  { to: '/dashboard', label: 'Dashboard' },
]

export default function Sidebar() {
  return (
    <aside className="w-52 bg-white border-r border-slate-200 hidden md:block">
      <nav className="p-4 space-y-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-lg transition ${isActive ? 'bg-amber-100 text-amber-800 font-medium' : 'text-slate-600 hover:bg-slate-100'}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
