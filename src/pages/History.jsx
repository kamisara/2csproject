// ----------------------------------------
// History Page Component
// Displays user's last 10 scan history items
// ----------------------------------------

"use client"

import { useState, useEffect } from "react"

export default function History() {
  // -------------------------------
  // State
  // -------------------------------
  const [historyItems, setHistoryItems] = useState([]) // Store scan history items
  const [loading, setLoading] = useState(true)         // Loading indicator
  const [error, setError] = useState("")               // Error message
  const API_BASE_URL = "http://127.0.0.1:8000"         // Backend API base URL

  // -------------------------------
  // Fetch scan history from Django backend
  // -------------------------------
  useEffect(() => {
    const fetchScanHistory = async () => {
      try {
        setLoading(true)

        // Send GET request to fetch latest 10 scans
        const res = await fetch(`${API_BASE_URL}/scans?limit=10`, {
          method: "GET",
          credentials: "include", // Include session cookies for authentication
        })

        if (!res.ok) throw new Error("Failed to fetch scan history")

        const data = await res.json()
        setHistoryItems(data.scans || []) // Save scans to state
      } catch (err) {
        console.error("Error fetching scan history:", err)
        setError(err.message || "Failed to load scan history")
      } finally {
        setLoading(false)
      }
    }

    fetchScanHistory()
  }, [])

  // -------------------------------
  // Handle downloading scan reports
  // Supports PDF, JSON, or HTML
  // -------------------------------
  const handleDownload = async (scanId, format = "pdf") => {
    try {
      const numericScanId = scanId.replace("s_", "") // Remove 's_' prefix
      const res = await fetch(`${API_BASE_URL}/scans/${numericScanId}/download`, {
        method: "GET",
        credentials: "include",
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData?.detail || "Failed to download report")
      }

      // -------------------------------
      // Handle file download based on format
      // -------------------------------
      if (format === "json") {
        const data = await res.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `scan_${scanId}_report.json`
        link.click()
        window.URL.revokeObjectURL(url)
      } else if (format === "html") {
        const html = await res.text()
        const blob = new Blob([html], { type: "text/html" })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `scan_${scanId}_report.html`
        link.click()
        window.URL.revokeObjectURL(url)
      } else {
        // Default PDF
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `scan_${scanId}_report.pdf`
        link.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error("Error downloading report:", err)
      setError(err.message || "Failed to download report")
    }
  }

  // -------------------------------
  // Utility: Format date nicely
  // -------------------------------
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // -------------------------------
  // Utility: Set color based on scan status
  // -------------------------------
  const getStatusColor = (status) => {
    switch (status) {
      case "completed": return "text-green-400"
      case "running": return "text-blue-400"
      case "queued": return "text-yellow-400"
      case "failed": return "text-red-400"
      case "canceled": return "text-gray-400"
      default: return "text-gray-400"
    }
  }

  // -------------------------------
  // Loading state
  // -------------------------------
  if (loading)
    return (
      <div className="min-h-screen bg-[#0D1B2A] text-[#F4F4F4] px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-4xl font-bold mb-8">Scan History</h1>
          <div className="text-center text-gray-400 mt-16">
            <p>Loading scan history...</p>
          </div>
        </div>
      </div>
    )

  // -------------------------------
  // Error state
  // -------------------------------
  if (error)
    return (
      <div className="min-h-screen bg-[#0D1B2A] text-[#F4F4F4] px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-4xl font-bold mb-8">Scan History</h1>
          <div className="text-center text-red-400 mt-16">
            <p>Error: {error}</p>
          </div>
        </div>
      </div>
    )

  // -------------------------------
  // Main scan history content
  // -------------------------------
  return (
    <div className="min-h-screen bg-[#0D1B2A] text-[#F4F4F4] px-6 py-16">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Scan History</h1>

        {/* -------------------------------
            No scan history yet
            ------------------------------- */}
        {historyItems.length === 0 ? (
          <div className="text-center text-gray-400 mt-16">
            <p>No scan history available.</p>
            <p className="mt-2">Start your first scan to see results here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {historyItems.map((item) => (
              <div
                key={item.scanId}
                className="bg-[#142D4C] border border-[#1F3B5A] rounded-2xl p-6 hover:bg-[#1A3C5E] transition-colors"
              >
                {/* -------------------------------
                    Header: Target, mode, status, date
                    ------------------------------- */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-lg font-semibold mb-1">{item.target}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span className="capitalize">{item.mode} scan</span>
                      <span className={`capitalize ${getStatusColor(item.status)}`}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                  <span className="text-sm text-gray-400">{formatDate(item.createdAt)}</span>
                </div>

                {/* -------------------------------
                    Description / info
                    ------------------------------- */}
                <div className="mb-4">
                  <span className="text-sm text-gray-400">
                    Vulnerability details available in full report
                  </span>
                </div>

                {/* -------------------------------
                    Action buttons: View, Download, Details
                    ------------------------------- */}
                <div className="flex gap-3">
                  {/* Open Django report in new tab */}
                  <button
                    onClick={() =>
                      window.open(
                        `http://127.0.0.1:8000/scans/${item.scanId.replace("s_", "")}/report`,
                        "_blank"
                      )
                    }
                    className="bg-[#34D399] text-[#0D1B2A] px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#2ab57d] transition-colors"
                  >
                    View Full Report
                  </button>

                  {/* Download PDF */}
                  <button
                    onClick={() => handleDownload(item.scanId, "pdf")}
                    className="bg-[#1F3B5A] text-[#F4F4F4] px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#2d537e] transition-colors"
                  >
                    Download PDF
                  </button>

                  {/* Scan details page */}
                  <button
                    onClick={() =>
                      window.open(
                        `http://127.0.0.1:8000/scans/${item.scanId.replace("s_", "")}`,
                        "_blank"
                      )
                    }
                    className="border border-[#1F3B5A] text-[#F4F4F4] px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#1F3B5A] transition-colors"
                  >
                    Scan Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
