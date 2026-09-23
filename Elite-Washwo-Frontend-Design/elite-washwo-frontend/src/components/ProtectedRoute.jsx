import React from 'react';
import { useAuth } from '../context/AuthContext';
// In a real router setup, we'd use Navigate from react-router-dom.
// Since the current app uses simple state routing, we'll return null or an access denied view.

export const ProtectedRoute = ({ children, requiredRole, requiredPermission }) => {
  const { session, role, loading, hasPermission } = useAuth();

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading session...</div>;
  }

  if (!session) {
    // In a real router: return <Navigate to="/login" replace />;
    return <div className="p-8 text-center text-red-500 font-bold">Please log in to access this page.</div>;
  }

  if (requiredRole && role !== requiredRole && role !== 'Super_Admin') {
    return <div className="p-8 text-center text-red-500 font-bold">Access Denied: Insufficient Role.</div>;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <div className="p-8 text-center text-red-500 font-bold">Access Denied: Missing Permission '{requiredPermission}'.</div>;
  }

  return children;
};
