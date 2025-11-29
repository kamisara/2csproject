import { useNavigate } from "react-router-dom";

export default function ScanButton() {
  const navigate = useNavigate(); // Hook to programmatically navigate to other routes

  return (
    // Outer container with glowing border and hover scale effect
    <div className="border-3 rounded-full p-1 shadow-[0_0_15px_2px_rgba(94,234,212,0.5)] transition-all duration-500 hover:scale-105">

      {/* Wrapper to align the button to the left */}
      <div className="flex justify-start">

        {/* Main Scan button */}
        <button
          onClick={() => navigate("/scan")}  // Navigate to /scan when clicked
          className="relative px-16 py-6 rounded-full text-lg font-semibold text-slate-900 bg-white
                     transition-all duration-500 
                     hover:shadow-[0_0_15px_4px_rgba(94,234,212,0.5)] hover:scale-90"
        >
          Scan Now
        </button>

      </div>
    </div>
  );
}
