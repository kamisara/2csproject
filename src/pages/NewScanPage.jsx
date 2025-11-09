"use client"

import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"

export default function NewScanPage() {
  const [scanType, setScanType] = useState("quick")
  const [url, setUrl] = useState("")
  const [isScanning, setIsScanning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState(30)
  const [error, setError] = useState("")
  const [userName, setUserName] = useState("UserName")
  const [scanComplete, setScanComplete] = useState(false)
  const [currentScan, setCurrentScan] = useState(null)
  const [recentScans, setRecentScans] = useState([])
  const navigate = useNavigate()
  const API_BASE_URL = "http://127.0.0.1:8000"

  // Track if cancel was requested to prevent polling interference
  const cancelRequestedRef = useRef(false)

  // Fetch user data and recent scans
  useEffect(() => {
    const fetchUserAndScans = async () => {
      try {
        // Fetch user profile
        const profileRes = await fetch(`${API_BASE_URL}/profile`, {
          method: "GET",
          credentials: "include",
        })
        
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          setUserName(`${profileData.user.firstName} ${profileData.user.lastName}` || "UserName")
        }

        // Fetch recent scans
        const scansRes = await fetch(`${API_BASE_URL}/scans?limit=5`, {
          method: "GET",
          credentials: "include",
        })
        
        if (scansRes.ok) {
          const scansData = await scansRes.json()
          setRecentScans(scansData.scans || [])
        }
      } catch (err) {
        console.error("Error fetching data:", err)
      }
    }

    fetchUserAndScans()
  }, [])

  // Poll for scan progress
  useEffect(() => {
    let interval
    if (isScanning && currentScan) {
      // Reset cancel flag when starting new scan
      cancelRequestedRef.current = false
      
      interval = setInterval(async () => {
        try {
          // Stop polling immediately if cancel was requested
          if (cancelRequestedRef.current) {
            clearInterval(interval)
            return
          }

          const scanId = currentScan.scanId.replace('s_', '')
          const res = await fetch(`${API_BASE_URL}/scans/${scanId}`, {
            method: "GET",
            credentials: "include",
          })
          
          if (res.ok) {
            const scanData = await res.json()
            
            // Update progress
            setProgress(scanData.progress || 0)
            
            if (scanData.estimatedTimeLeft) {
              setEstimatedTime(scanData.estimatedTimeLeft)
            }
            
            // Check if scan is complete
            if (scanData.status === "completed") {
              setIsScanning(false)
              setScanComplete(true)
              setProgress(100)
              clearInterval(interval)
              
              // Refresh recent scans
              const scansRes = await fetch(`${API_BASE_URL}/scans?limit=5`, {
                method: "GET",
                credentials: "include",
              })
              if (scansRes.ok) {
                const scansData = await scansRes.json()
                setRecentScans(scansData.scans || [])
              }
            } else if (scanData.status === "failed" || scanData.status === "canceled") {
              setIsScanning(false)
              setError(`Scan ${scanData.status}`)
              clearInterval(interval)
              setCurrentScan(null)
            }
          }
        } catch (err) {
          console.error("Error polling scan status:", err)
        }
      }, 2000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isScanning, currentScan])

  const handleStartScan = async () => {
    if (!url.trim()) {
      setError("Please enter a valid URL, IP address, or CIDR range")
      return
    }

    setError("")
    setIsScanning(true)
    setProgress(0)
    setEstimatedTime(scanType === "quick" ? 30 : 120)

    try {
      const res = await fetch(`${API_BASE_URL}/scans`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: url.trim(),
          mode: scanType,
        }),
      })

      const responseData = await res.json()
      
      if (!res.ok) {
        throw new Error(responseData?.error?.message || "Failed to start scan")
      }

      setCurrentScan(responseData)
      setError("")
    } catch (err) {
      console.error("Error starting scan:", err)
      setError(err.message || "Failed to start scan")
      setIsScanning(false)
    }
  }

  const handleCancelScan = async () => {
    if (!currentScan) return

    try {
      // Set cancel flag immediately to stop polling
      cancelRequestedRef.current = true

      const scanId = currentScan.scanId.replace('s_', '')
      const res = await fetch(`${API_BASE_URL}/scans/${scanId}/cancel`, {
        method: "POST",
        credentials: "include",
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData?.error?.message || "Failed to cancel scan")
      }

      // Immediately update UI state
      setIsScanning(false)
      setProgress(0)
      setEstimatedTime(30)
      setCurrentScan(null)
      setError("Scan cancelled successfully")
      
      // Refresh recent scans
      const scansRes = await fetch(`${API_BASE_URL}/scans?limit=5`, {
        method: "GET",
        credentials: "include",
      })
      if (scansRes.ok) {
        const scansData = await scansRes.json()
        setRecentScans(scansData.scans || [])
      }
    } catch (err) {
      console.error("Error cancelling scan:", err)
      setError(err.message || "Failed to cancel scan")
      // Even if API call fails, reset the UI state
      setIsScanning(false)
      setCurrentScan(null)
      cancelRequestedRef.current = false
    }
  }

  const handleScanAgain = () => {
    setScanComplete(false)
    setIsScanning(false)
    setProgress(0)
    setEstimatedTime(30)
    setUrl("")
    setError("")
    setCurrentScan(null)
    cancelRequestedRef.current = false
  }

  const handleViewReport = (scanId) => {
    const numericScanId = scanId.replace('s_', '')
    navigate(`/scans/${numericScanId}`)
  }

  const handleDownloadReport = async (scanId, format = "pdf") => {
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

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins} minute${mins !== 1 ? "s" : ""} ${secs} second${secs !== 1 ? "s" : ""}`
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (scanComplete && currentScan) {
    return (
      <div className="bg-[#0D1B2A] min-h-screen">
        <div className="text-[#F4F4F4]">
          {/* Success Screen */}
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
              {/* Shield Icon */}
              <div className="relative mb-8">
                <div className="flex items-center justify-center h-32 w-32 rounded-full bg-[#34D399]/10 ring-4 ring-[#34D399]/30">
                  <svg
                    className="h-20 w-20 text-[#34D399]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <path d="M9 12l2 2 4-4" />
                  </svg>
                </div>
              </div>

              {/* Success Banner */}
              <div className="relative mb-8 bg-[#34D399] rounded-xl px-12 py-6 shadow-lg shadow-[#34D399]/30">
                <div className="absolute -top-3 -right-3 bg-white rounded-full p-2 shadow-lg">
                  <svg
                    className="h-6 w-6 text-[#34D399]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                  >
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white text-center">Scan Completed Successfully!</h1>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 mb-8">
                <button 
                  onClick={() => handleViewReport(currentScan.scanId)}
                  className="rounded-lg bg-red-500 px-8 py-3 font-semibold text-white hover:bg-red-600 transition-all shadow-lg shadow-red-500/30"
                >
                  View Scan Report
                </button>
                <button 
                  onClick={() => handleDownloadReport(currentScan.scanId, "pdf")}
                  className="rounded-lg border border-[#34D399] px-6 py-3 font-semibold text-[#34D399] hover:bg-[#34D399]/10 transition-all"
                >
                  Download PDF
                </button>
              </div>

              {/* Scan Details */}
              <div className="text-center text-gray-400 mb-4">
                <p className="font-medium">Target: {currentScan.target}</p>
                <p className="text-sm">Mode: {currentScan.mode}</p>
              </div>

              <button
                onClick={handleScanAgain}
                className="mt-4 rounded-lg border border-[#34D399] px-6 py-2 text-sm font-medium text-[#34D399] hover:bg-[#34D399]/10 transition-all"
              >
                Scan Again
              </button>
            </div>
          </div>

          {/* Recent Scans Section */}
          <div className="mx-auto max-w-7xl px-6 pb-16">
            <h2 className="text-2xl font-bold mb-6">Recent Scans</h2>
            <div className="space-y-4">
              {recentScans.map((scan) => (
                <div key={scan.scanId} className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 flex-1">
                      <div className={`flex items-center justify-center h-12 w-12 rounded-full ${
                        scan.status === "completed" ? "bg-[#34D399]/20 ring-4 ring-[#34D399]/30" :
                        scan.status === "running" ? "bg-blue-500/20 ring-4 ring-blue-500/30" :
                        "bg-gray-500/20 ring-4 ring-gray-500/30"
                      }`}>
                        <svg
                          className={`h-6 w-6 ${
                            scan.status === "completed" ? "text-[#34D399]" :
                            scan.status === "running" ? "text-blue-500" :
                            "text-gray-500"
                          }`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                          {scan.status === "completed" && <path d="M9 12l2 2 4-4" />}
                        </svg>
                      </div>
                      <div>
                        <span className="font-medium block">{scan.target}</span>
                        <span className="text-sm text-gray-400 capitalize">{scan.mode} scan</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 flex-1">
                      <span className="text-gray-400">{formatDate(scan.createdAt)}</span>
                    </div>
                    <div className="flex items-center gap-6 flex-1 justify-end">
                      <span className={`capitalize ${getStatusColor(scan.status)}`}>
                        {scan.status}
                      </span>
                      {scan.status === "completed" && (
                        <button 
                          onClick={() => handleViewReport(scan.scanId)}
                          className="rounded-lg border border-[#1F3B5A] px-6 py-2 text-sm font-medium hover:bg-[#34D399]/10 hover:border-[#34D399] transition-all"
                        >
                          View Report
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#0D1B2A] min-h-screen">
      <div className="text-[#F4F4F4]">
        {/* Error Message */}
        {error && (
          <div className={`fixed top-5 left-1/2 -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg z-50 ${
            error.includes("Error") || error.includes("Failed") 
              ? "bg-red-500 text-white" 
              : "bg-[#34D399] text-white"
          }`}>
            {error}
          </div>
        )}

        {/* Hero Section */}
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="flex items-center justify-between gap-12">
            {isScanning ? (
              <>
                {/* Scanning Animation - LEFT SIDE */}
                <div className="relative w-64 h-64 flex items-center justify-center">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-56 h-56 rounded-full border-[3px] border-[#34D399]/40 animate-ping"></div>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-44 h-44 rounded-full border-[3px] border-[#34D399]/30 animate-pulse"></div>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-32 h-32 rounded-full border-[3px] border-[#34D399]/20 animate-bounce"></div>
                    </div>

                    <div className="relative flex items-center justify-center w-40 h-40 rounded-full bg-[#34D399]/5 border-[3px] border-[#34D399]">
                      <svg
                        className="absolute h-24 w-24 text-[#34D399]"
                        viewBox="0 0 100 100"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                      >
                        <path d="M 20 35 L 20 20 L 35 20" />
                        <path d="M 65 20 L 80 20 L 80 35" />
                        <path d="M 20 65 L 20 80 L 35 80" />
                        <path d="M 65 80 L 80 80 L 80 65" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Scanning Text - RIGHT SIDE */}
                <div className="flex-1">
                  <h1 className="text-5xl font-bold mb-4">Scanning in progress...</h1>
                  <p className="text-gray-400 text-lg mb-8">Uncover key vulnerabilities and security flaws.</p>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[#F4F4F4] font-medium">{progress}% Complete</span>
                    </div>
                    <div className="w-full bg-[#1F3B5A] rounded-full h-2.5 overflow-hidden">
                      <div
                        className="bg-[#34D399] h-full rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                    <p className="text-gray-400 text-sm">Estimated time remaining: {formatTime(estimatedTime)}</p>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="flex-1">
                  <h1 className="text-5xl font-bold mb-4">New Scan</h1>
                  <p className="text-gray-400 text-lg">Easily scan websites and applications for common security flaws.</p>
                </div>

                {/* Right Side PC with bubbles */}
                <div className="relative w-64 h-64 flex items-center justify-center">
                  <div className="absolute w-48 h-32 border-4 border-[#34D399] rounded-lg shadow-[0_0_25px_#34D399] bg-[#0B1C2C] flex items-center justify-center"></div>
                  <div className="absolute bottom-6 w-56 h-3 bg-[#34D399] rounded-md shadow-[0_0_15px_#34D399]"></div>

                  <div className="absolute w-4 h-4 bg-[#34D399] rounded-full opacity-70 animate-bounce top-6 left-6"></div>
                  <div className="absolute w-6 h-6 bg-[#34D399] rounded-full opacity-60 animate-pulse top-20 right-10"></div>
                  <div className="absolute w-3 h-3 bg-[#34D399] rounded-full opacity-50 animate-bounce bottom-10 left-10"></div>
                  <div className="absolute w-5 h-5 bg-[#34D399] rounded-full opacity-70 animate-ping bottom-16 right-16"></div>
                  <div className="absolute w-3 h-3 bg-[#34D399] rounded-full opacity-60 animate-bounce top-10 right-20"></div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Scan Form */}
        <div className="mx-auto max-w-7xl px-6 pb-16">
          <div className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-8">
            <label className="block text-sm font-medium mb-3">Enter URL, IP Address, or CIDR Range to Scan</label>
            <div className="flex gap-4 mb-2">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="e.g. https://your-website.com, 192.168.1.1, or 10.0.0.0/24"
                disabled={isScanning}
                className="flex-1 rounded-lg bg-[#0D1B2A] border border-[#1F3B5A] px-4 py-3 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#34D399] focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              />
              {isScanning ? (
                <button
                  onClick={handleCancelScan}
                  className="rounded-lg bg-red-500 px-8 py-3 font-semibold text-white hover:bg-red-600 transition-all shadow-lg shadow-red-500/30"
                >
                  Cancel Scan
                </button>
              ) : (
                <button
                  onClick={handleStartScan}
                  className="rounded-lg bg-[#34D399] px-8 py-3 font-semibold text-white hover:bg-[#2bb380] transition-all shadow-lg shadow-[#34D399]/30"
                >
                  Start Scan
                </button>
              )}
            </div>

            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

            <div className="flex gap-8">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="scanType"
                  value="quick"
                  checked={scanType === "quick"}
                  onChange={(e) => setScanType(e.target.value)}
                  disabled={isScanning}
                  className="h-5 w-5 appearance-none rounded-full border-2 border-[#1F3B5A] bg-[#0D1B2A] checked:border-[#34D399] checked:bg-[#34D399] cursor-pointer transition-all"
                />
                <div>
                  <div className="font-medium group-hover:text-[#34D399]">Quick Scan</div>
                  <div className="text-sm text-gray-400">Fast results with limited checks.</div>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="scanType"
                  value="full"
                  checked={scanType === "full"}
                  onChange={(e) => setScanType(e.target.value)}
                  disabled={isScanning}
                  className="h-5 w-5 appearance-none rounded-full border-2 border-[#1F3B5A] bg-[#0D1B2A] checked:border-[#34D399] checked:bg-[#34D399] cursor-pointer transition-all"
                />
                <div>
                  <div className="font-medium group-hover:text-[#34D399]">Full Scan</div>
                  <div className="text-sm text-gray-400">Maximum/Detailed report for web applications.</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="mx-auto max-w-7xl px-6 pb-16">
          <h2 className="text-2xl font-bold mb-6">Recent Scans</h2>
          <div className="space-y-4">
            {recentScans.length > 0 ? (
              recentScans.map((scan) => (
                <div key={scan.scanId} className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 flex-1">
                      <div className={`flex items-center justify-center h-12 w-12 rounded-full ${
                        scan.status === "completed" ? "bg-[#34D399]/20 ring-4 ring-[#34D399]/30" :
                        scan.status === "running" ? "bg-blue-500/20 ring-4 ring-blue-500/30" :
                        "bg-gray-500/20 ring-4 ring-gray-500/30"
                      }`}>
                        <svg
                          className={`h-6 w-6 ${
                            scan.status === "completed" ? "text-[#34D399]" :
                            scan.status === "running" ? "text-blue-500" :
                            "text-gray-500"
                          }`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                          {scan.status === "completed" && <path d="M9 12l2 2 4-4" />}
                        </svg>
                      </div>
                      <div>
                        <span className="font-medium block">{scan.target}</span>
                        <span className="text-sm text-gray-400 capitalize">{scan.mode} scan</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 flex-1">
                      <span className="text-gray-400">{formatDate(scan.createdAt)}</span>
                    </div>
                    <div className="flex items-center gap-6 flex-1 justify-end">
                      <span className={`capitalize ${getStatusColor(scan.status)}`}>
                        {scan.status}
                      </span>
                      {scan.status === "completed" && (
                        <button 
                          onClick={() => handleViewReport(scan.scanId)}
                          className="rounded-lg border border-[#1F3B5A] px-6 py-2 text-sm font-medium hover:bg-[#34D399]/10 hover:border-[#34D399] transition-all"
                        >
                          View Report
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl bg-[#142D4C] border border-[#1F3B5A] p-6 text-center text-gray-400">
                No recent scans found. Start your first scan above!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
