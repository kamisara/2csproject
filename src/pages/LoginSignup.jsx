"use client";

import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginSignup() {
  const [isLogin, setIsLogin] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const API_BASE_URL = "http://127.0.0.1:8000";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password || (!isLogin && (!firstName || !lastName))) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      const endpoint = isLogin ? "/login" : "/register";
      const payload = isLogin
        ? { email, password }
        : { email, password, firstName, lastName };

      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include", // important for Django session cookie
      });

      const data = await res.json();

      if (!res.ok) {
        const msg =
          data?.error?.message ||
          (isLogin ? "Invalid email or password" : "Registration failed");
        throw new Error(msg);
      }

      if (isLogin) {
        // ✅ Login successful → redirect to home page
        navigate("/home");
      } else {
        // ✅ Registration successful → redirect to login page
        alert("Registration successful! Please log in.");
        setIsLogin(true);
        setEmail("");
        setPassword("");
        setFirstName("");
        setLastName("");
        navigate("/login");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong");
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-start overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center filter brightness-110 contrast-110 saturate-110"
        style={{ backgroundImage: "url('src/assets/background_login_page.avif')" }}
      />
      <div className="absolute inset-0 bg-[#142D4C] opacity-30" />

      {/* Logo */}
      <div className="absolute top-8 left-8 z-20 flex items-center gap-2">
        <svg className="h-8 w-8 text-[#34D399]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span className="text-2xl font-bold text-[#F4F4F4]">VulnScan</span>
      </div>

      {/* Auth Form */}
      <div className="relative z-10 w-full max-w-md bg-[#142D4C] rounded-2xl shadow-2xl p-8 border border-[#1F3B5A] ml-28 transform scale-110 ring-2 ring-[#A8E6CF] hover:ring-green-400 transition shadow-lg shadow-green-400/30">
        <h2 className="text-3xl font-bold text-[#F4F4F4] mb-6 text-center">
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <input
                type="text"
                placeholder="First Name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-4 py-2 bg-[#0D1B2A] text-[#F4F4F4] border border-[#1F3B5A] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
              />
              <input
                type="text"
                placeholder="Last Name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-4 py-2 bg-[#0D1B2A] text-[#F4F4F4] border border-[#1F3B5A] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
              />
            </>
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-2 bg-[#0D1B2A] text-[#F4F4F4] border border-[#1F3B5A] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 bg-[#0D1B2A] text-[#F4F4F4] border border-[#1F3B5A] rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
          />

          <button
            type="submit"
            className="w-full bg-[#0D1B2A] text-[#F4F4F4] py-2 rounded-lg border border-green-400 hover:bg-green-400 hover:text-[#0D1B2A] transition shadow-lg shadow-green-400/40"
          >
            {isLogin ? "Login" : "Sign Up"}
          </button>
        </form>

        <p className="text-sm text-[#F4F4F4] mt-4 text-center">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-green-400 font-semibold hover:underline"
          >
            {isLogin ? "Sign Up" : "Login"}
          </button>
        </p>
      </div>
    </div>
  );
}







