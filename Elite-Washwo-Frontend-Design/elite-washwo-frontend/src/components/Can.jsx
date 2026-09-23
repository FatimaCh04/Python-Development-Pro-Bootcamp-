import React from 'react';
import { useAuth } from '../context/AuthContext';

export const Can = ({ I, a, children, fallback = null }) => {
  const { hasPermission } = useAuth();

  // "I" is the action, "a" is the module (e.g. I="view" a="sales" -> 'sales.view')
  const permissionString = `${a}.${I}`;
  
  if (hasPermission(permissionString)) {
    return children;
  }
  
  return fallback;
};
