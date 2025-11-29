import React from 'react'

// components/Footer.jsx
export default function Footer() {
  return (
    // Footer container with top border and dark background
    <footer className="border-t border-[#1F3B5A] bg-[#142D4C] mt-auto">
      <div className="mx-auto max-w-7xl px-6 py-6">
        
        {/* Flex container: left = copyright, right = links */}
        <div className="flex items-center justify-between text-sm text-gray-400">
          
          {/* Website copyright text */}
          <span>© 2025 VulnScan</span>

          {/* Navigation links (Privacy Policy, Terms) */}
          <div className="flex gap-8">
            {/* Privacy Policy link */}
            <a href="#" className="hover:text-[#F4F4F4] transition-colors">
              Privacy Policy
            </a>

            {/* Terms of Service link */}
            <a href="#" className="hover:text-[#F4F4F4] transition-colors">
              Terms of Service
            </a>
          </div>

        </div>

      </div>
    </footer>
  );
}
