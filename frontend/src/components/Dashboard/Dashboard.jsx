import React from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useDispatch } from 'react-redux'
import { useSelector } from 'react-redux';
import { clearAuthState } from '../../redux/userSlice.js';

const Dashboard = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate();

  const userInfo = useSelector((state) => state.user.userInfo);

  if (!userInfo) {
    navigate("/login");
    return null;
  }

  const { role, email } = userInfo;

  
const handleLogout = async () => {
  try {
    await axios.post('http://localhost:8000/user/logout', {}, { withCredentials: true });

    dispatch(clearAuthState()); 
    navigate("/");
  } catch (error) {
    console.error("Logout failed:", error);
  }
};

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <section className="bg-white rounded-lg shadow-md max-w-md w-full p-8 text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Welcome, {email}
        </h1>
        <p className="text-gray-600 mb-8 capitalize">Role: {role}</p>

        <div className="flex flex-col gap-4">
          <button
            onClick={() => navigate("/upload")}
            className="py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition"
          >
            Upload File
          </button>

          <button
            onClick={() => navigate("/download")}
            className="py-2 rounded-md bg-green-600 text-white hover:bg-green-700 transition"
          >
            Download File
          </button>

          {role === "superadmin" && (
            <button
              onClick={() => navigate("/admin")}
              className="py-2 rounded-md bg-purple-600 text-white hover:bg-purple-700 transition"
            >
              Update Role
            </button>
          )}

          <button
            onClick={handleLogout}
            className="py-2 rounded-md bg-red-600 text-white hover:bg-red-700 transition mt-6"
          >
            Logout
          </button>
        </div>
      </section>
    </main>
  );
};

export default Dashboard;
