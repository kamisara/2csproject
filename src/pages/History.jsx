"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"

export default function History() {
  const [historyItems, setHistoryItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const navigate = useNavigate()
  const API_BASE_URL = "http://127.0.0.1:8000"

  useEffect(() => {
    const fetchScanHistory = async () => {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE_URL}/scans?limit=10`, {
          method: "GET",
          credentials: "include",
        })

        if (!res.ok) {
          throw new Error("Failed to fetch scan history")
        }

        const data = await res.json()
        setHistoryItems(data.scans || [])
      } catch (err) {
        console.error("Error fetching scan history:", err)
        setError(err.message || "Failed to load scan history")
      } finally {
        setLoading(false)
      }
    }

    fetchScanHistory()
  }, [])

  const handleDownload = async (scanId, format = "pdf") => {
    try {
      const numericScanId = scanId.replace('s_', '')
      const res = await fetch(`${API_BASE_URL}/scans/${numericScanId}/download?format=${format}`, {
        method: "GET",
        credentials: "include",
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData?.detail || "Failed to download report")
      }

      // Handle different response types
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
        // PDF
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

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

  if (loading) {
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
  }

  if (error) {
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
  }

  return (
    <div className="min-h-screen bg-[#0D1B2A] text-[#F4F4F4] px-6 py-16">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Scan History</h1>

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

                {/* Note about vulnerabilities - since they're not in the list response */}
                <div className="mb-4">
                  <span className="text-sm text-gray-400">
                    Vulnerability details available in full report
                  </span>
                </div>

                {/* Action buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={() => navigate(`/scans/${item.scanId.replace('s_', '')}/report`)}
                    className="bg-[#34D399] text-[#0D1B2A] px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#2ab57d] transition-colors"
                  >
                    View Full Report
                  </button>
                  <button
                    onClick={() => handleDownload(item.scanId, "pdf")}
                    className="bg-[#1F3B5A] text-[#F4F4F4] px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#2d537e] transition-colors"
                  >
                    Download PDF
                  </button>
                  <button
                    onClick={() => navigate(`/scans/${item.scanId.replace('s_', '')}`)}
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
