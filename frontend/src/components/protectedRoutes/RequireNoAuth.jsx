import React from "react";
import { Navigate } from "react-router-dom";

const RequireNoAuth = ({ children }) => {
  const userInfo = localStorage.getItem("userInfo");

  if (userInfo) {
    // User is logged in, redirect to dashboard (or wherever)
    return <Navigate to="/dashboard" replace />;
  }

  // User not logged in, allow access
  return children;
};

export default RequireNoAuth;
