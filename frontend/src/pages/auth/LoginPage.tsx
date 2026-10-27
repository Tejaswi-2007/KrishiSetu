/** Login page */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../stores/auth';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Sprout } from 'lucide-react';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/profile');
    } catch (err: any) {
      setError(err.detail || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Sprout className="w-12 h-12 text-forest mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-forest">Welcome Back</h1>
          <p className="text-gray-600">Login to your KrishiSetu account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border p-8 space-y-4">
          {error && (
            <div className="bg-red-50 text-error px-4 py-2 rounded-lg text-sm">{error}</div>
          )}
          <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="your@email.com" />
          <Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </Button>
          <p className="text-center text-sm text-gray-600">
            Don't have an account? <Link to="/register" className="text-forest font-medium hover:underline">Register</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
