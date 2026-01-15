import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="min-h-screen bg-terminal-bg terminal-grid">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 ml-64 mt-16">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
