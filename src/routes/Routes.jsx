import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import NewScanPage from "../pages/NewScanPage";
import History from "../pages/History";
import AboutUs from "../pages/AboutUs";
import Profile from "../pages/Profile";
import LoginSignup from "../pages/LoginSignup";
import ProtectedRoute from "./ProtectedRoute"; // ✅ Protect sensitive routes

export default function AppRoutes() {
  return (
    <Routes>
      {/* ======================== */}
      {/* Public Routes (accessible without login) */}
      {/* ======================== */}
      <Route path="/home" element={<Home />} />           {/* Landing / dashboard */}
      <Route path="/about" element={<AboutUs />} />      {/* About us page */}
      <Route path="/login" element={<LoginSignup />} />  {/* Login / Signup page */}

      {/* ======================== */}
      {/* Protected Routes (require authentication) */}
      {/* ======================== */}
      <Route element={<ProtectedRoute />}>
        {/* All child routes will first pass through ProtectedRoute */}
        <Route path="/scan" element={<NewScanPage />} /> {/* New scan page */}
        <Route path="/history" element={<History />} />  {/* Scan history */}
        <Route path="/profile" element={<Profile />} />  {/* User profile */}
      </Route>

      {/* ======================== */}
      {/* Fallback Route */}
      {/* ======================== */}
      <Route path="*" element={<Home />} /> {/* Redirect any unknown route to home */}
    </Routes>
  );
}
