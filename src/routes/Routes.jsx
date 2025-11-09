import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import NewScanPage from "../pages/NewScanPage";
import History from "../pages/History";
import AboutUs from "../pages/AboutUs";
import Profile from "../pages/Profile";
import LoginSignup from "../pages/LoginSignup";
import ProtectedRoute from "./ProtectedRoute"; // ✅ Import this

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/home" element={<Home />} />
      <Route path="/about" element={<AboutUs />} />
      <Route path="/login" element={<LoginSignup />} />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/scan" element={<NewScanPage />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      {/* Default redirect (optional) */}
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
