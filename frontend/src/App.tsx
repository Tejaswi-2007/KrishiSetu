
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './stores/auth';

import { HomePage } from './pages/public/HomePage';
import { MarketplacePage } from './pages/marketplace/MarketplacePage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import MarketPricesPage from './pages/market-prices/MarketPricesPage';
import AuctionsPage from './pages/auctions/AuctionsPage';
import BuyerRequestsPage from './pages/buyer-requests/BuyerRequestsPage';
import CommunityPage from './pages/farmer-community/CommunityPage';
import SchemesPage from './pages/schemes/SchemesPage';
import NewsPage from './pages/news/NewsPage';
import ProfilePage from './pages/profile/ProfilePage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen">
          <nav className="bg-forest text-white p-4 flex flex-wrap gap-4 items-center">
            <Link to="/" className="font-bold text-xl">
              KrishiSetu
            </Link>
            <Link to="/marketplace" className="hover:underline">
              Marketplace
            </Link>
            <Link to="/market-prices" className="hover:underline">
              Market Prices
            </Link>
            <Link to="/auctions" className="hover:underline">
              Auctions
            </Link>
            <Link to="/buyer-requests" className="hover:underline">
              Buyer Requests
            </Link>
            <Link to="/farmer-community" className="hover:underline">
              Community
            </Link>
            <Link to="/schemes" className="hover:underline">
              Schemes
            </Link>
            <Link to="/news" className="hover:underline">
              News
            </Link>
            <Link to="/profile" className="hover:underline">
              My Profile
            </Link>
            <Link to="/login" className="hover:underline">
              Login
            </Link>
            <Link to="/register" className="hover:underline">
              Register
            </Link>
          </nav>

          <main className="p-4">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/marketplace" element={<MarketplacePage />} />
              <Route path="/market-prices" element={<MarketPricesPage />} />
              <Route path="/auctions" element={<AuctionsPage />} />
              <Route path="/buyer-requests" element={<BuyerRequestsPage />} />
              <Route path="/farmer-community" element={<CommunityPage />} />
              <Route path="/schemes" element={<SchemesPage />} />
              <Route path="/news" element={<NewsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route
                path="*"
                element={
                  <div className="p-6">
                    <h1 className="text-2xl font-bold">Page not found</h1>
                    <Link to="/" className="text-green-800 underline">
                      Return to KrishiSetu Home
                    </Link>
                  </div>
                }
              />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
