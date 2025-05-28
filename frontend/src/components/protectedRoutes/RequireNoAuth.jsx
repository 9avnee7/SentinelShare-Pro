import React from "react";
import { Navigate } from "react-router-dom";
import { useSelector } from "react-redux";

const RequireNoAuth = ({ children }) => {
  const userInfo = useSelector((state) => state.user.userInfo);

  if (userInfo) {
    // User is logged in, redirect to dashboard (or wherever you want)
    return <Navigate to="/dashboard" replace />;
  }

  // User not logged in, allow access
  return children;
};

export default RequireNoAuth;
