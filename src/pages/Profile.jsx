"use client";
import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [profileImage, setProfileImage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [deletePassword, setDeletePassword] = useState(""); // for delete account
  const [deleteConfirm, setDeleteConfirm] = useState(false); // changed to boolean
  const [deletePhrase, setDeletePhrase] = useState(""); // for DELETE phrase
  const [message, setMessage] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState([]);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const API_BASE_URL = "http://127.0.0.1:8000";

  // ---------- Fetch Profile ----------
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/profile`, {
          method: "GET",
          credentials: "include",
        });
        if (res.status === 401) {
          navigate("/login");
          return;
        }
        if (!res.ok) throw new Error("Failed to fetch profile");
        const data = await res.json();
        setProfile(data.user);
        // Use avatarUrl from the response instead of photo_url
        setProfileImage(data.user.avatarUrl || null);
      } catch (err) {
        console.error(err);
        navigate("/login");
      }
    };
    fetchProfile();
  }, [navigate]);

  // ---------- Message Timeout ----------
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(""), 3500);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // ---------- Password Validation ----------
  const validatePassword = (password) => {
    const errors = [];
    
    if (password.length < 6) {
      errors.push("Password must be at least 6 characters long");
    }
    
    if (/^\d+$/.test(password)) {
      errors.push("Password cannot be entirely numeric");
    }
    
    if (password.toLowerCase().includes("password")) {
      errors.push("Password cannot contain the word 'password'");
    }
    
    if (password.toLowerCase().includes(profile?.email?.split('@')[0]?.toLowerCase() || '')) {
      errors.push("Password cannot contain your email address");
    }
    
    // Common weak password check
    const weakPasswords = ['123456', 'password', '12345678', 'qwerty', 'abc123'];
    if (weakPasswords.includes(password.toLowerCase())) {
      errors.push("Password is too common");
    }
    
    return errors;
  };

  // ---------- Handlers ----------

  // Save name
  const handleSaveProfile = async () => {
    if (!profile) return;
    try {
      const res = await fetch(`${API_BASE_URL}/profile/name`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: profile.first_name,
          last_name: profile.last_name,
        }),
      });
      
      console.log("Profile update response status:", res.status);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData?.error?.message || "Failed to update profile");
      }
      
      setMessage("Profile updated successfully!");
      setIsEditing(false);
    } catch (err) {
      console.error("Profile update error:", err);
      setMessage(err.message || "Error updating profile");
    }
  };

  // Profile image preview & upload - FIXED
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview instantly
    const reader = new FileReader();
    reader.onload = (ev) => setProfileImage(ev.target.result);
    reader.readAsDataURL(file);

    // Upload to server
    const formData = new FormData();
    formData.append("photo", file);
    try {
      const res = await fetch(`${API_BASE_URL}/profile/photo`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      
      console.log("Photo upload response status:", res.status);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData?.error?.message || "Failed to upload photo");
      }
      
      const data = await res.json();
      console.log("Photo upload response data:", data);
      
      // Update both the profile image and the profile state
      setProfileImage(data.user.avatarUrl);
      setProfile(prevProfile => ({
        ...prevProfile,
        avatarUrl: data.user.avatarUrl
      }));
      setMessage("Profile photo updated!");
    } catch (err) {
      console.error("Photo upload error:", err);
      setMessage(err.message || "Error uploading photo");
    }
  };

  // Change password - FIXED with better validation
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordErrors([]);
    
    // Validation
    if (!oldPassword || !newPassword || !confirmPassword) {
      setMessage("Please fill in all password fields");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }
    
    // Client-side password validation
    const validationErrors = validatePassword(newPassword);
    if (validationErrors.length > 0) {
      setPasswordErrors(validationErrors);
      setMessage("Please fix the password errors below");
      return;
    }

    try {
      console.log("Sending password change request...");
      
      const requestBody = {
        currentPassword: oldPassword,
        newPassword: newPassword,
        newPasswordConfirm: confirmPassword,
      };
      
      console.log("Request body:", requestBody);
      
      const res = await fetch(`${API_BASE_URL}/profile/change-password`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      console.log("Password change response status:", res.status);
      
      const responseData = await res.json();
      console.log("Password change response data:", responseData);

      if (!res.ok) {
        // Handle Django validation errors
        if (responseData?.error?.message?.non_field_errors) {
          const backendErrors = responseData.error.message.non_field_errors;
          setPasswordErrors(Array.isArray(backendErrors) ? backendErrors : [backendErrors]);
          throw new Error("Please fix the password errors below");
        }
        
        const errorMessage = typeof responseData?.error?.message === 'object' 
          ? JSON.stringify(responseData.error.message)
          : responseData?.error?.message || `HTTP error! status: ${res.status}`;
        throw new Error(errorMessage);
      }

      setMessage("Password changed successfully!");
      setShowPasswordForm(false);
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordErrors([]);
      
    } catch (err) {
      console.error("Password change error:", err);
      // Only show generic message if we haven't set specific password errors
      if (passwordErrors.length === 0) {
        const errorMsg = err.message.includes('{') ? "Password change failed. Please check all fields." : err.message;
        setMessage(errorMsg);
      }
    }
  };

  // Handle new password input with real-time validation
  const handleNewPasswordChange = (e) => {
    const value = e.target.value;
    setNewPassword(value);
    
    // Real-time validation
    if (value.length > 0) {
      const errors = validatePassword(value);
      setPasswordErrors(errors);
    } else {
      setPasswordErrors([]);
    }
  };

  // Logout
  const handleLogout = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/logout`, {
        method: "POST",
        credentials: "include",
      });
      
      console.log("Logout response status:", res.status);
      
      if (!res.ok) {
        throw new Error("Logout failed");
      }
      
      setMessage("Logged out successfully");
      setTimeout(() => navigate("/login"), 1000);
    } catch (err) {
      console.error("Logout error:", err);
      setMessage("Logout failed");
    }
  };

  // Delete account
  const handleDeleteAccount = () => setShowDeleteConfirm(true);

  const confirmDeleteAccount = async () => {
    if (!deletePassword) {
      setMessage("Please enter your password to delete account");
      return;
    }

    if (!deleteConfirm) {
      setMessage("Please check the confirmation box");
      return;
    }

    if (deletePhrase !== "DELETE") {
      setMessage("Please type 'DELETE' exactly as shown to confirm");
      return;
    }
    
    setShowDeleteConfirm(false);
    
    try {
      console.log("Sending delete account request...");
      
      const requestBody = {
        currentPassword: deletePassword,
        confirm: deleteConfirm, // This should be boolean true
        phrase: deletePhrase,   // This should be the string "DELETE"
      };
      
      console.log("Delete request body:", requestBody);
      
      const res = await fetch(`${API_BASE_URL}/profile/delete-account`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      console.log("Delete account response status:", res.status);
      
      let responseData = {};
      try {
        // For successful delete (204), there might be no response body
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          responseData = await res.json();
        } else if (res.status !== 204) {
          responseData = { error: { message: `HTTP ${res.status}` } };
        }
      } catch (e) {
        console.log("No JSON response body for delete");
      }

      console.log("Delete account response data:", responseData);

      if (!res.ok) {
        // Handle Django validation errors
        if (responseData?.error?.message?.confirm) {
          throw new Error("Please check the confirmation box");
        }
        if (responseData?.error?.message?.phrase) {
          throw new Error("Please type 'DELETE' exactly as shown");
        }
        if (responseData?.error?.message?.currentPassword) {
          throw new Error("Incorrect password. Please try again.");
        }
        
        const errorMessage = typeof responseData?.error?.message === 'object' 
          ? JSON.stringify(responseData.error.message)
          : responseData?.error?.message || `HTTP error! status: ${res.status}`;
        throw new Error(errorMessage);
      }

      setMessage("Account deleted successfully");
      setTimeout(() => navigate("/signup"), 1000);
      
    } catch (err) {
      console.error("Delete account error:", err);
      setMessage(err.message || "Error deleting account");
      setDeletePassword(""); // Clear password on error
      setDeleteConfirm(false); // Clear confirmation on error
      setDeletePhrase(""); // Clear phrase on error
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setDeletePassword("");
    setDeleteConfirm(false);
    setDeletePhrase("");
  };

  // Password strength indicator
  const getPasswordStrength = (password) => {
    if (!password) return 0;
    
    let strength = 0;
    if (password.length >= 6) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    return strength;
  };

  const passwordStrength = getPasswordStrength(newPassword);

  // ---------- Render ----------
  if (!profile) return <p>Loading profile...</p>;

  return (
    <div className="min-h-screen bg-[#0D1B2A] text-[#F4F4F4] relative">
      {message && (
        <div className={`fixed top-5 left-1/2 -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg z-50 ${
          message.includes("Error") || message.includes("Failed") || message.includes("incorrect") || message.includes("Please") 
            ? "bg-red-500 text-white" 
            : "bg-[#34D399] text-white"
        }`}>
          {message}
        </div>
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/60 z-50">
          <div className="bg-[#142D4C] p-8 rounded-xl shadow-lg max-w-md w-full">
            <h2 className="text-xl font-semibold mb-4 text-red-400 text-center">Delete Your Account</h2>
            <p className="text-gray-300 mb-6 text-center">
              This action cannot be undone. This will permanently delete your account and all associated data.
            </p>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2">Enter your password</label>
                <input
                  type="password"
                  placeholder="Your current password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="w-full rounded-lg px-4 py-2 bg-[#0D1B2A] border border-[#1F3B5A] text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                  autoFocus
                />
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <input
                  type="checkbox"
                  id="deleteConfirm"
                  checked={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.checked)}
                  className="mt-1 text-red-500 focus:ring-red-500"
                />
                <label htmlFor="deleteConfirm" className="text-sm text-red-300">
                  I understand that this action cannot be undone and I want to permanently delete my account.
                </label>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Type <span className="font-mono text-red-400">DELETE</span> to confirm
                </label>
                <input
                  type="text"
                  placeholder="Type DELETE here"
                  value={deletePhrase}
                  onChange={(e) => setDeletePhrase(e.target.value)}
                  className="w-full rounded-lg px-4 py-2 bg-[#0D1B2A] border border-[#1F3B5A] text-white focus:outline-none focus:ring-2 focus:ring-red-500 font-mono"
                />
                {deletePhrase && deletePhrase !== "DELETE" && (
                  <p className="text-red-400 text-xs mt-1">Please type DELETE exactly as shown</p>
                )}
              </div>
            </div>
            
            <div className="flex justify-center gap-4">
              <button
                onClick={confirmDeleteAccount}
                disabled={!deletePassword || !deleteConfirm || deletePhrase !== "DELETE"}
                className="bg-red-500 text-white px-6 py-2 rounded-lg hover:bg-red-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Account
              </button>
              <button
                onClick={cancelDelete}
                className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-4xl px-6 py-16">
        <h1 className="text-4xl font-bold mb-12">Profile Settings</h1>

        {/* Profile Photo */}
        <div className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-8 mb-8 flex items-center gap-8">
          <div className="relative group w-32 h-32 rounded-full border-4 border-[#34D399] overflow-hidden bg-[#0D1B2A] flex items-center justify-center">
            {profileImage ? (
              <img 
                src={profileImage} 
                alt="Profile" 
                className="w-full h-full object-cover"
                onError={(e) => {
                  // If the image fails to load, fall back to default avatar
                  console.error("Image failed to load:", profileImage);
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <svg
                className="w-16 h-16 text-gray-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            )}
            <label className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
                ref={fileInputRef}
              />
            </label>
          </div>

          <div>
            <p className="text-lg font-medium">Update your profile photo</p>
            <p className="text-sm text-gray-400 mt-1">Click on the image to upload a new photo</p>
            {profileImage && (
              <p className="text-xs text-blue-400 mt-2">
                Current photo: {profileImage}
              </p>
            )}
          </div>
        </div>

        {/* Personal Info */}
        <div className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-8 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Personal Information</h2>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="rounded-lg border border-[#34D399] px-4 py-2 text-sm font-medium text-[#34D399] hover:bg-[#34D399]/10 transition-all"
            >
              {isEditing ? "Cancel" : "Edit"}
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">First Name</label>
              <input
                type="text"
                value={profile.first_name || ""}
                onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                disabled={!isEditing}
                className="w-full rounded-lg bg-[#0D1B2A] border border-[#1F3B5A] px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#34D399] disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Last Name</label>
              <input
                type="text"
                value={profile.last_name || ""}
                onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                disabled={!isEditing}
                className="w-full rounded-lg bg-[#0D1B2A] border border-[#1F3B5A] px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#34D399] disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={profile.email || ""}
                disabled
                className="w-full rounded-lg bg-[#0D1B2A] border border-[#1F3B5A] px-4 py-2 opacity-50 cursor-not-allowed"
              />
            </div>
            {isEditing && (
              <button
                onClick={handleSaveProfile}
                className="rounded-lg bg-[#34D399] px-6 py-2 text-white font-semibold hover:bg-[#2bb380] transition-all"
              >
                Save Changes
              </button>
            )}
          </div>
        </div>

        {/* Security */}
        <div className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-8">
          <h2 className="text-2xl font-semibold mb-6">Security Settings</h2>
          
          {/* Change Password Section */}
          <div className="mb-6">
            <button
              onClick={() => {
                setShowPasswordForm(!showPasswordForm);
                setPasswordErrors([]);
                setNewPassword("");
                setConfirmPassword("");
                setOldPassword("");
              }}
              className="w-full text-left px-6 py-4 border border-[#1F3B5A] rounded-lg hover:bg-[#34D399]/10 transition-all flex justify-between items-center"
            >
              <span>Change Password</span>
              <svg 
                className={`w-5 h-5 transition-transform ${showPasswordForm ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showPasswordForm && (
              <form onSubmit={handleChangePassword} className="mt-4 p-4 bg-[#0D1B2A] rounded-lg space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Current Password</label>
                  <input
                    type="password"
                    placeholder="Enter current password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full rounded-lg px-4 py-2 bg-[#142D4C] border border-[#1F3B5A] focus:outline-none focus:ring-2 focus:ring-[#34D399]"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">New Password</label>
                  <input
                    type="password"
                    placeholder="Enter new password"
                    value={newPassword}
                    onChange={handleNewPasswordChange}
                    className="w-full rounded-lg px-4 py-2 bg-[#142D4C] border border-[#1F3B5A] focus:outline-none focus:ring-2 focus:ring-[#34D399]"
                    required
                    minLength={6}
                  />
                  
                  {/* Password Strength Indicator */}
                  {newPassword && (
                    <div className="mt-2">
                      <div className="flex gap-1 mb-1">
                        {[1, 2, 3, 4, 5].map((index) => (
                          <div
                            key={index}
                            className={`h-1 flex-1 rounded-full ${
                              index <= passwordStrength 
                                ? passwordStrength >= 4 
                                  ? 'bg-green-500' 
                                  : passwordStrength >= 3 
                                    ? 'bg-yellow-500' 
                                    : 'bg-red-500'
                                : 'bg-gray-600'
                            }`}
                          />
                        ))}
                      </div>
                      <p className="text-xs text-gray-400">
                        {passwordStrength === 0 && "Enter a password"}
                        {passwordStrength === 1 && "Very weak"}
                        {passwordStrength === 2 && "Weak"}
                        {passwordStrength === 3 && "Medium"}
                        {passwordStrength === 4 && "Strong"}
                        {passwordStrength === 5 && "Very strong"}
                      </p>
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Confirm New Password</label>
                  <input
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full rounded-lg px-4 py-2 bg-[#142D4C] border ${
                      confirmPassword && newPassword !== confirmPassword 
                        ? 'border-red-500' 
                        : 'border-[#1F3B5A]'
                    } focus:outline-none focus:ring-2 focus:ring-[#34D399]`}
                    required
                    minLength={6}
                  />
                  {confirmPassword && newPassword !== confirmPassword && (
                    <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
                  )}
                </div>
                
                {/* Password Error Messages */}
                {passwordErrors.length > 0 && (
                  <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm font-medium mb-2">Please fix the following:</p>
                    <ul className="text-red-400 text-sm list-disc list-inside space-y-1">
                      {passwordErrors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <button
                  type="submit"
                  disabled={passwordErrors.length > 0 || newPassword !== confirmPassword}
                  className="rounded-lg bg-[#34D399] px-6 py-2 text-white font-semibold hover:bg-[#2bb380] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Password
                </button>
              </form>
            )}
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full text-left px-6 py-4 border border-[#1F3B5A] rounded-lg hover:bg-blue-500/20 transition-all mb-4"
          >
            Log Out
          </button>
          
          {/* Delete Account Button */}
          <button
            onClick={handleDeleteAccount}
            className="w-full text-left px-6 py-4 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/20 transition-all"
          >
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}