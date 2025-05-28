import React from 'react';
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';

const RequireRole = ({ roleAllowed, children }) => {
  const userInfo = useSelector((state) => state.user.userInfo);

  if (!userInfo) {
    // Not logged in
    return <Navigate to="/login" replace />;
  }

  if (!roleAllowed.includes(userInfo.role)) {
    // Logged in but not authorized
    return (
      <div className="text-center mt-10 text-xl text-red-500">
        Access Denied: You do not have the required permissions.
      </div>
    );
  }

  return children;
};

export default RequireRole;
