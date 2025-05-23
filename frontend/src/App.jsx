
import './App.css'
import { Children, useEffect } from 'react';
import axios from 'axios';
import {createBrowserRouter , RouterProvider } from "react-router-dom";
import { useContext } from 'react';
import { GlobalContext } from './index';
import Upload from './components/upload/Upload';
import Download from './components/upload/Download';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Hero from './components/Hero/Hero';
import AdminRoleManager from './components/RoleManager/adminRoleManager'; 
import RequireRole from './components/protectedRoutes/requiredRole';
import Dashboard from './components/Dashboard/Dashboard';
import RequireNoAuth from './components/protectedRoutes/RequireNoAuth';

const router=createBrowserRouter([
  {
    path:'/login',
    element: <div>
      <RequireNoAuth>
      <Login/>
      </RequireNoAuth>
    </div>
  },
  {
    path:'/',
    element: <div>
      <Hero/>
    
    </div>
  },
  {
    path:'/admin',
    element: <div>
      <RequireRole roleAllowed={['superadmin']}>
      <AdminRoleManager />
    </RequireRole>
    
    </div>
  },
  {
    path:'/register',
    element: <div>
      <RequireNoAuth>
      <Register/>
      </RequireNoAuth>
    </div>
  },
  {
    path:'/upload',
    element: <div>
      <RequireRole roleAllowed={['user','admin','superadmin']}>
      <Upload/>
      </RequireRole>
    </div>
  },
  {
    path:'/download',
    element: <div>
      <RequireRole roleAllowed={['user','admin','superadmin']}>
      <Download/>
      </RequireRole>
    </div>
  },

  {
    path:'/dashboard',
    element:
        <div>
          <RequireRole roleAllowed={['user','admin','superadmin']}>
          <Dashboard/>
          </RequireRole>
         </div>

  }
])

function App() {

  const { setAccessToken, setUserInfo, setLoggedIn, setLoading } = useContext(GlobalContext);
  const userInfo = JSON.parse(sessionStorage.getItem('userInfo')) || null;
  
  const refresh = async () => {
  try {
    console.log("Refreshing token on refresh");
    const res = await axios.post(
      "http://localhost:8000/user/refresh",
      {}, // empty body
      { withCredentials: true }
    );

    const data = res.data;

    if (!data.user_info) {
      setUserInfo(null);
      setAccessToken(null);
      setLoggedIn(false);
      return;
    }

    sessionStorage.setItem("userInfo", JSON.stringify(data.user_info));
    setUserInfo(data.user_info);
    setAccessToken(data.access_token);
    setLoggedIn(true);

    console.log("User Info Updated:", data.user_info);
  } catch (e) {
    console.error("Error occurred on refreshing refreshToken", e);
    setAccessToken(null);
    setLoggedIn(false);
  } finally {
    setLoading(false);
  }
};

useEffect(() => {
  refresh();
  const interval = setInterval(() => {
    refresh();
  }, 14 * 60 * 1000);

  return () => clearInterval(interval);
}, []);


   useEffect(() => {
    console.log("Updated userInfo:", userInfo);
    sessionStorage.setItem('userInfo',JSON.stringify(userInfo))
}, [userInfo]);

  return (
    <>
     <RouterProvider router={router}/>

    </>
  )
}

export default App






