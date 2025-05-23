import { useEffect, useState } from 'react';
import axios from 'axios';

export default function AdminRoleManager() {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState('');

  const fetchUsers = async () => {
    try {
      const res = await axios.get('http://localhost:8000/admin/users', {
        withCredentials: true, // <- sends cookies
      });
      setUsers(res.data);
    } catch (err) {
      console.error(err);
      setMessage('Failed to load users. Make sure you are superadmin.');
    }
  };

  const updateRole = async (id, role) => {
    try {
      await axios.patch(
        `http://localhost:8000/admin/update-role/${id}?role=${role}`,
        {},
        {
          withCredentials: true, // <- sends cookies
        }
      );
      setMessage(`Updated role to ${role}`);
      fetchUsers();
    } catch (err) {
      console.error(err);
      setMessage('Failed to update role.');
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div className="max-w-3xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-center">Manage User Roles</h2>
      {message && <p className="text-center text-red-500 mb-4">{message}</p>}
      <table className="w-full table-auto border">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 border">ID</th>
            <th className="p-2 border">Email</th>
            <th className="p-2 border">Role</th>
            <th className="p-2 border">Action</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td className="p-2 border text-center">{user.id}</td>
              <td className="p-2 border text-center">{user.email}</td>
              <td className="p-2 border text-center">{user.role}</td>
              <td className="p-2 border text-center space-x-2">
                <button
                  onClick={() => updateRole(user.id, 'user')}
                  className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                >
                  Make User
                </button>
                <button
                  onClick={() => updateRole(user.id, 'admin')}
                  className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                >
                  Make Admin
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
