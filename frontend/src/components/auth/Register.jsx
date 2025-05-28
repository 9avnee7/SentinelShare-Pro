import { useState, useContext } from 'react';
import axios from 'axios';
import QRCode from 'react-qr-code';
import { GlobalContext } from '../../index.jsx';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setAuthState } from '../../redux/userSlice';

export default function Register() {
  const dispatch = useDispatch()

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [message, setMessage] = useState('');
  const [totpUri, setTotpUri] = useState('');
  const navigate = useNavigate();

  const handleChange = e => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await axios.post('http://localhost:8000/user/register', {
        ...formData,
        role: 'user',
      }, { withCredentials: true });

      setMessage('Registration successful');
      setTotpUri(res.data.totp_uri);
        dispatch(setAuthState({
      userInfo: res.data.user_info,
      accessToken: res.data.access_token
    }));
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Error during registration');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    navigate('/dashboard'); // ✅ update path if different
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-white p-6 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-4 text-center">Register</h2>
      {message && <p className="text-center text-red-600 font-semibold mb-2">{message}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-md bg-blue-50 focus:outline-none"
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white font-semibold py-2 rounded-md hover:bg-blue-700 flex justify-center items-center"
        >
          {loading ? (
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-white rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-3 h-3 bg-white rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-3 h-3 bg-white rounded-full animate-bounce"></div>
            </div>
          ) : (
            'Register'
          )}
        </button>
      </form>

      {totpUri && (
        <div className="mt-6 text-center">
          <p className="text-green-700 font-semibold">Scan this QR in Google Authenticator:</p>
          <div className="flex justify-center mt-2">
            <QRCode value={totpUri} size={180} />
          </div>
          <p className="mt-2 text-xs text-gray-500 break-words">{totpUri}</p>
          <button
            onClick={handleNext}
            className="mt-4 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
