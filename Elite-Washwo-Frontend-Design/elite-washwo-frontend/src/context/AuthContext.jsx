import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check active sessions and sets the user
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) {
        fetchProfileAndPermissions(session.user.id);
      } else {
        setLoading(false);
      }
    });

    // Listen for changes on auth state
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchProfileAndPermissions(session.user.id);
      } else {
        setUser(null);
        setRole(null);
        setPermissions([]);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchProfileAndPermissions = async (userId) => {
    try {
      // Fetch profile
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();
      
      if (profileError) throw profileError;
      
      setUser(profile);
      setRole(profile.role);

      // Fetch permissions if Manager
      if (profile.role === 'Manager') {
        const { data: perms, error: permError } = await supabase
          .from('user_permissions')
          .select('permission_id')
          .eq('user_id', userId);
          
        if (permError) throw permError;
        setPermissions(perms.map(p => p.permission_id));
      } else if (profile.role === 'Super_Admin') {
        // Super Admin gets all permissions implicitly
        setPermissions(['ALL']);
      } else {
        setPermissions([]); // Salesman relies on RLS directly, no explicit arbitrary permissions
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (requiredPermission) => {
    if (role === 'Super_Admin') return true;
    if (role === 'Manager') return permissions.includes(requiredPermission);
    return false; // Salesmen don't use this dynamic permission array
  };

  const login = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  };

  const logout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  return (
    <AuthContext.Provider value={{ session, user, role, permissions, loading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
