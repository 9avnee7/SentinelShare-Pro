import React from 'react';
import { Navigate } from 'react-router-dom';

const RequireRole = ({ roleAllowed, children }) => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo'));

  if (!userInfo) {
    // Not logged in -> redirect to login
    return <Navigate to="/login" replace />;
  }

  if (!roleAllowed.includes(userInfo.role)) {
    // Logged in but not authorized
    return <p>Access Denied</p>;
  }

  return children;
};

export default RequireRole;
