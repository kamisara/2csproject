"use client"; // Ensures this component runs in client-side rendering
import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

export default function ProtectedRoute() {
  // State to track if the auth check is still loading
  const [isLoading, setIsLoading] = useState(true);

  // State to track if the user is authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Async function to check user authentication
    const checkAuth = async () => {
      try {
        // Call backend profile endpoint to verify session/auth
        const res = await fetch("http://127.0.0.1:8000/profile", {
          method: "GET",
          credentials: "include", // Send cookies/session info (important for Django)
        });

        // If backend returns 200 OK, user is authenticated
        if (res.ok) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } catch (err) {
        console.error("Auth check failed:", err);
        setIsAuthenticated(false);
      } finally {
        // Auth check completed, stop loading spinner
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []); // Run only once when component mounts

  // Show loading indicator while auth check is in progress
  if (isLoading) return <p>Loading...</p>;

  // If authenticated, render the nested route(s)
  // Otherwise, redirect user to login page
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
