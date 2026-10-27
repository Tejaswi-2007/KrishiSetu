/** Registration page */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../stores/auth';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Sprout } from 'lucide-react';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'farmer' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/profile');
    } catch (err: any) {
      setError(err.detail || err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Sprout className="w-12 h-12 text-forest mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-forest">Join KrishiSetu</h1>
          <p className="text-gray-600">Create your account to start trading</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border p-8 space-y-4">
          {error && <div className="bg-red-50 text-error px-4 py-2 rounded-lg text-sm">{error}</div>}
          <Input label="Full Name" value={form.full_name} onChange={set('full_name')} required placeholder="Your full name" />
          <Input label="Email" type="email" value={form.email} onChange={set('email')} required placeholder="your@email.com" />
          <Input label="Password" type="password" value={form.password} onChange={set('password')} required placeholder="Min 8 chars, uppercase, lowercase, digit" />

          <div className="space-y-1">
            <label className="block text-sm font-medium text-dark-text">I am a</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'farmer', label: '🌾 Farmer' },
                { value: 'buyer', label: '🏪 Buyer' },
                { value: 'fpo_admin', label: '👥 FPO' },
              ].map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, role: opt.value }))}
                  className={`py-2 px-3 rounded-lg border text-sm font-medium transition ${
                    form.role === opt.value
                      ? 'bg-forest text-white border-forest'
                      : 'bg-white text-dark-text border-gray-300 hover:border-forest'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
          <p className="text-center text-sm text-gray-600">
            Already have an account? <Link to="/login" className="text-forest font-medium hover:underline">Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
