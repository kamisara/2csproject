import { useState, useEffect } from "react"

export default function Vulnerabilities({ user }) {
  // ----------------------------------
  // State variables
  // ----------------------------------
  const [vulnerabilities, setVulnerabilities] = useState([]) // Holds the list of vulnerabilities
  const [loading, setLoading] = useState(true)               // Loading indicator
  const [error, setError] = useState(null)                  // Error messages
  const API_BASE_URL = "http://127.0.0.1:8000"              // Base API URL

  // ----------------------------------
  // Fetch vulnerabilities on mount or when 'user' changes
  // ----------------------------------
  useEffect(() => {
    const fetchLatestVulnerabilities = async () => {
      if (!user) {
        // User not logged in → show placeholder vulnerabilities
        setVulnerabilities([
          { name: 'SQL Injection', status: 'unknown' },
          { name: 'Cross-Site Scripting (XSS)', status: 'unknown' },
          { name: 'Outdated Libraries', status: 'unknown' },
          { name: 'TLS/SSL Issues', status: 'unknown' },
          { name: 'Information Disclosure', status: 'unknown' },
        ])
        setLoading(false)
        return
      }

      try {
        // Fetch latest scan for logged-in user
        const scansRes = await fetch(`${API_BASE_URL}/scans?limit=1`, {
          credentials: "include",
        })

        if (scansRes.ok) {
          const scansData = await scansRes.json()
          if (scansData.scans && scansData.scans.length > 0) {
            const latestScan = scansData.scans[0]

            if (latestScan.status === "completed") {
              const scanId = latestScan.scanId.replace('s_', '')
              const reportRes = await fetch(`${API_BASE_URL}/scans/${scanId}/report`, {
                credentials: "include",
              })

              if (reportRes.ok) {
                const reportData = await reportRes.json()
                // Store fetched vulnerabilities in state
                setVulnerabilities(reportData.vulnerabilities || [])
              }
            }
          }
        }

        setError(null) // Clear previous errors
      } catch (error) {
        console.error("💥 Error fetching vulnerabilities:", error)
        setError(`Network error: ${error.message}`)
        // Fallback static data
        setVulnerabilities([
          { name: 'SQL Injection', status: 'unknown' },
          { name: 'Cross-Site Scripting (XSS)', status: 'unknown' },
          { name: 'Outdated Libraries', status: 'unknown' },
          { name: 'TLS/SSL Issues', status: 'unknown' },
          { name: 'Information Disclosure', status: 'unknown' },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchLatestVulnerabilities()
  }, [user])

  // ----------------------------------
  // Common vulnerabilities list (static)
  // ----------------------------------
  const commonVulns = [
    { name: 'SQL Injection', type: 'sql_injection' },
    { name: 'Cross-Site Scripting (XSS)', type: 'xss' },
    { name: 'Outdated Libraries', type: 'outdated' },
    { name: 'TLS/SSL Issues', type: 'tls' },
    { name: 'Information Disclosure', type: 'info_disclosure' }
  ]

  // ----------------------------------
  // Determine vulnerability status for display
  // ----------------------------------
  const getVulnStatus = (vulnName, detectedVulns = vulnerabilities) => {
    if (!detectedVulns || detectedVulns.length === 0) {
      return { status: 'unknown', icon: '?' } // No data
    }

    const foundVuln = detectedVulns.find(v =>
      v.name.toLowerCase().includes(vulnName.toLowerCase().split(' ')[0])
    )

    return {
      status: foundVuln ? foundVuln.status : 'unknown',
      icon: foundVuln ? (foundVuln.status === 'warning' ? '!' : '✓') : '?',
      count: foundVuln ? foundVuln.count : 0
    }
  }

  // ----------------------------------
  // Render loading skeleton
  // ----------------------------------
  if (loading) {
    return (
      <div className="w-full">
        <div className="bg-slate-800 rounded-2xl p-6 shadow-2xl">
          <h3 className="text-xl font-bold text-white mb-6">Common Vulnerabilities</h3>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse bg-slate-700/50 p-4 rounded-lg">
                <div className="h-4 bg-slate-600 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ----------------------------------
  // Render vulnerabilities list
  // ----------------------------------
  return (
    <div className="w-full">
      <div className="bg-slate-800 rounded-2xl p-6 shadow-2xl">
        <h3 className="text-xl font-bold text-white mb-6">
          Common Vulnerabilities {vulnerabilities.length > 0 && user && `(${vulnerabilities.length} found)`}
        </h3>

        <div className="space-y-3">
          {commonVulns.map((vuln, index) => {
            const status = getVulnStatus(vuln.name)

            return (
              <div
                key={index}
                className="flex items-center justify-between bg-slate-700/50 p-4 rounded-lg hover:bg-slate-700 transition-colors"
              >
                {/* Vulnerability name and details */}
                <div className="flex items-center gap-3">
                  {/* Status indicator circle */}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    status.status === 'safe' ? 'bg-teal-500' :
                    status.status === 'warning' ? 'bg-orange-500' :
                    'bg-gray-500'
                  }`}>
                    <span className="text-white font-bold text-sm">{status.icon}</span>
                  </div>

                  {/* Name + count + message */}
                  <div>
                    <span className="text-sm text-slate-200 block">{vuln.name}</span>
                    {status.count > 0 && (
                      <span className="text-xs text-cyan-400">
                        Found {status.count} time{status.count !== 1 ? 's' : ''}
                      </span>
                    )}
                    {status.status === 'safe' && status.count === 0 && (
                      <span className="text-xs text-green-400">No instances found</span>
                    )}
                    {status.status === 'unknown' && (
                      <span className="text-xs text-gray-400">No scan data</span>
                    )}
                  </div>
                </div>

                {/* Status icon */}
                <div>
                  {status.status === 'safe' ? (
                    <span className="text-green-400 text-lg">✅</span>
                  ) : status.status === 'warning' ? (
                    <span className="text-orange-400 text-lg">⚠️</span>
                  ) : (
                    <span className="text-gray-400 text-lg">❔</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Fallback message if no vulnerabilities found */}
        {vulnerabilities.length === 0 && user && (
          <div className="text-center text-slate-400 mt-4 text-sm">
            No vulnerability data available. Run some scans to see results!
          </div>
        )}

        {/* Debug info - development only */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-4 p-2 bg-blue-500/10 rounded text-xs text-blue-300">
            <div>User: {user ? "Logged in" : "Not logged in"}</div>
            <div>Vulnerabilities loaded: {vulnerabilities.length}</div>
            <div>API Response: {vulnerabilities.length > 0 ? "Has data" : "Empty"}</div>
            <div>API: {API_BASE_URL}/most-common-vuln/</div>
          </div>
        )}
      </div>
    </div>
  )
}
