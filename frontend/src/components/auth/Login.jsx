import { useState, useContext } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { GlobalContext } from '../../index.jsx';
import { GoogleLogin } from '@react-oauth/google';

export default function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    twofa_code: '',
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const { setAccessToken, setLoggedIn, setUserInfo } = useContext(GlobalContext);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const data = new URLSearchParams();
    for (const key in formData) {
      data.append(key, formData[key]);
    }

    try {
      const res = await axios.post('http://localhost:8000/user/login', data, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        withCredentials: true,
      });

      setMessage('Login successful');
      setAccessToken(res.data.access_token);
      setLoggedIn(true);
      setUserInfo(res.data.user_info);
      localStorage.setItem('userInfo', JSON.stringify(res.data.user_info));
      navigate('/dashboard');
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async (credentialResponse) => {
    try {
      const credential = credentialResponse.credential;

      const res = await axios.post(
        'http://localhost:8000/user/login/google',
        { token: credential },
        { withCredentials: true }
      );

      setAccessToken(res.data.access_token);
      setLoggedIn(true);
      setUserInfo(res.data.user_info);
      localStorage.setItem('userInfo', JSON.stringify(res.data.user_info));
      navigate('/dashboard');
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Google login failed');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-white p-6 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-4 text-center">Login</h2>
      {message && <p className="text-center text-sm text-red-600 mb-2">{message}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          name="username"
          placeholder="Email"
          className="w-full border border-gray-300 rounded-md px-4 py-2 bg-blue-50 focus:outline-none"
          value={formData.username}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          className="w-full border border-gray-300 rounded-md px-4 py-2 bg-white focus:outline-none"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="twofa_code"
          placeholder="2FA Code"
          className="w-full border border-gray-300 rounded-md px-4 py-2 bg-white focus:outline-none"
          value={formData.twofa_code}
          onChange={handleChange}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 rounded-md font-semibold text-white ${
            loading ? 'bg-gray-500' : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {loading ? (
            <div className="flex justify-center items-center space-x-1">
              <span className="animate-bounce">.</span>
              <span className="animate-bounce delay-100">.</span>
              <span className="animate-bounce delay-200">.</span>
            </div>
          ) : (
            'Login'
          )}
        </button>
      </form>

      <div className="text-center text-gray-500 my-4">OR</div>

      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={handleGoogleLogin}
          onError={() => setMessage('Google login error')}
        />
      </div>
    </div>
  );
}
