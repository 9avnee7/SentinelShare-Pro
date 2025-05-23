import { useNavigate } from 'react-router-dom';

export default function GetStarted() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-blue-50 flex flex-col justify-center items-center">
      <div className="text-center">
        <h1 className="text-4xl sm:text-5xl font-bold text-blue-700 mb-8">SentinelShare Pro</h1>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
          >
            Login
          </button>
          <button
            onClick={() => navigate('/register')}
            className="px-6 py-3 rounded-lg bg-green-600 text-white font-semibold hover:bg-green-700 transition"
          >
            Register
          </button>
        </div>
      </div>
    </div>
  );
}
