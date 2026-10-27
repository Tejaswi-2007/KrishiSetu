/** Main app layout with navigation */
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../stores/auth';
import { Menu, X, Bell, User, LogOut, Sprout, ShoppingCart, BarChart3, Handshake, LayoutDashboard, Shield } from 'lucide-react';
import { useState } from 'react';

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/'); };

  const navItems = getNavItems(user?.role || '');

  return (
    <div className="min-h-screen bg-cream">
      {/* Top Nav */}
      <header className="bg-forest text-white shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 font-bold text-xl">
            <Sprout className="w-7 h-7 text-gold" />
            <span>Digi-Mandi</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {!user ? (
              <>
                <NavLink to="/marketplace">Marketplace</NavLink>
                <NavLink to="/market-prices">Market Prices</NavLink>
                <NavLink to="/about">About</NavLink>
                <Link to="/login" className="ml-4 px-4 py-2 bg-gold text-dark-text rounded-lg font-medium hover:bg-amber-400 transition">
                  Login
                </Link>
              </>
            ) : (
              <>
                {navItems.map(item => (
                  <NavLink key={item.to} to={item.to}>{item.icon}{item.label}</NavLink>
                ))}
                <button onClick={() => navigate('/notifications')} className="p-2 hover:bg-leaf rounded-lg relative ml-2">
                  <Bell className="w-5 h-5" />
                </button>
                <div className="relative ml-2 group">
                  <button className="flex items-center gap-2 p-2 hover:bg-leaf rounded-lg">
                    <User className="w-5 h-5" />
                    <span className="text-sm max-w-24 truncate">{user.full_name}</span>
                  </button>
                  <div className="absolute right-0 top-full mt-1 w-48 bg-white text-dark-text rounded-lg shadow-xl border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                    <Link to="/profile" className="block px-4 py-2 hover:bg-pale-green rounded-t-lg">Profile</Link>
                    <button onClick={handleLogout} className="w-full text-left px-4 py-2 hover:bg-pale-green rounded-b-lg flex items-center gap-2 text-error">
                      <LogOut className="w-4 h-4" /> Logout
                    </button>
                  </div>
                </div>
              </>
            )}
          </nav>

          {/* Mobile hamburger */}
          <button className="md:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden bg-forest border-t border-leaf px-4 pb-4">
            {!user ? (
              <>
                <MobileLink to="/marketplace" onClick={() => setMobileOpen(false)}>Marketplace</MobileLink>
                <MobileLink to="/market-prices" onClick={() => setMobileOpen(false)}>Market Prices</MobileLink>
                <MobileLink to="/login" onClick={() => setMobileOpen(false)}>Login</MobileLink>
              </>
            ) : (
              <>
                {navItems.map(item => (
                  <MobileLink key={item.to} to={item.to} onClick={() => setMobileOpen(false)}>
                    {item.icon}{item.label}
                  </MobileLink>
                ))}
                <button onClick={handleLogout} className="w-full text-left py-3 text-red-300 flex items-center gap-2">
                  <LogOut className="w-4 h-4" /> Logout
                </button>
              </>
            )}
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-forest text-white/70 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          <p className="font-medium text-white mb-1">Digi-Mandi — A Complete Ecosystem for Agriculture</p>
          <p>© {new Date().getFullYear()} Digi-Mandi. Connecting farmers with buyers across Maharashtra.</p>
        </div>
      </footer>
    </div>
  );
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link to={to} className="px-3 py-2 rounded-lg hover:bg-leaf transition text-sm flex items-center gap-1.5">
      {children}
    </Link>
  );
}

function MobileLink({ to, onClick, children }: { to: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link to={to} onClick={onClick} className="block py-3 border-b border-leaf/30 flex items-center gap-2">
      {children}
    </Link>
  );
}

function getNavItems(role: string) {
  const common = [
    { to: '/marketplace', label: 'Marketplace', icon: <ShoppingCart className="w-4 h-4" /> },
    { to: '/market-prices', label: 'Prices', icon: <BarChart3 className="w-4 h-4" /> },
  ];
  if (role === 'farmer') return [
    { to: '/farmer/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    ...common,
    { to: '/farmer/listings', label: 'My Listings', icon: <Sprout className="w-4 h-4" /> },
    { to: '/farmer/offers', label: 'Offers', icon: <Handshake className="w-4 h-4" /> },
    { to: '/deal-rooms', label: 'Deal Rooms', icon: <Handshake className="w-4 h-4" /> },
  ];
  if (role === 'buyer') return [
    { to: '/buyer/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    ...common,
    { to: '/buyer/offers', label: 'My Offers', icon: <Handshake className="w-4 h-4" /> },
    { to: '/deal-rooms', label: 'Deal Rooms', icon: <Handshake className="w-4 h-4" /> },
  ];
  if (role === 'admin') return [
    { to: '/admin/dashboard', label: 'Admin', icon: <Shield className="w-4 h-4" /> },
    ...common,
  ];
  return common;
}
