import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { token, logout } = useAuth()

  return (
    <header className="bg-slate-900 text-white shadow">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="font-semibold text-lg">AI Translator Pro</Link>
        <nav className="flex items-center gap-4">
          <Link to="/translator" className="hover:text-amber-300 transition">Translator</Link>
          <Link to="/speech" className="hover:text-amber-300 transition">Speech</Link>
          <Link to="/image" className="hover:text-amber-300 transition">Image</Link>
          {token ? (
            <>
              <Link to="/dashboard" className="hover:text-amber-300 transition">Dashboard</Link>
              <button onClick={logout} className="text-slate-300 hover:text-white">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-amber-300 transition">Login</Link>
              <Link to="/signup" className="bg-amber-500 hover:bg-amber-600 px-3 py-1.5 rounded transition">Sign up</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
