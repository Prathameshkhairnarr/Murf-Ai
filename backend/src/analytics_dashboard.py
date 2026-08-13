import sqlite3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Path to the sqlite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "callers.db")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rakshika - Call Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --success: #22c55e;
            --success-glow: rgba(34, 197, 94, 0.5);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.5);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --glass-bg: rgba(20, 25, 40, 0.6);
            --glass-border: rgba(255, 255, 255, 0.08);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Outfit', sans-serif;
            color: var(--text);
            min-height: 100vh;
            padding: 3rem 2rem;
            position: relative;
            overflow-x: hidden;
            background-color: #0b0f19;
        }

        /* Animated Mesh Gradient Background */
        .bg-mesh {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: -1;
            background: 
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(34, 197, 94, 0.1), transparent 25%),
                radial-gradient(circle at 50% 80%, rgba(239, 68, 68, 0.1), transparent 25%);
            filter: blur(60px);
            animation: mesh-move 15s ease-in-out infinite alternate;
        }

        @keyframes mesh-move {
            0% { transform: scale(1) translate(0, 0); }
            50% { transform: scale(1.1) translate(2%, -2%); }
            100% { transform: scale(1) translate(-2%, 2%); }
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
            position: relative;
            z-index: 10;
        }

        header {
            margin-bottom: 3.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--glass-border);
        }

        h1 {
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            font-weight: 500;
            color: #4ade80;
            background: rgba(34, 197, 94, 0.1);
            padding: 0.4rem 1rem;
            border-radius: 999px;
            border: 1px solid rgba(34, 197, 94, 0.2);
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.15);
        }

        .pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #4ade80;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.5); }
            70% { box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); }
            100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        /* Glassmorphism Cards */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: 1.25rem;
            padding: 2rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255,255,255,0.15);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
        }

        .metric-title {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.75rem;
        }

        .metric-value {
            font-size: 4.5rem;
            font-weight: 600;
            line-height: 1;
            letter-spacing: -0.03em;
        }

        .value-primary {
            background: linear-gradient(135deg, #fff, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .value-success {
            background: linear-gradient(135deg, #4ade80, #16a34a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 40px var(--success-glow);
        }
        .value-danger {
            background: linear-gradient(135deg, #f87171, #dc2626);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 40px var(--danger-glow);
        }
        
        .recent-calls h2 {
            font-size: 1.25rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
            color: #fff;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }

        th, td {
            padding: 1.2rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--glass-border);
        }

        th {
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        tbody tr {
            transition: background 0.2s ease;
        }

        tbody tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .status-success {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }

        .status-failed {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .anon-id {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            color: #e2e8f0;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="bg-mesh"></div>
    <div class="container">
        <header>
            <h1>Rakshika Analytics</h1>
            <div class="live-indicator">
                <div class="pulse"></div>
                LIVE FEED
            </div>
        </header>

        <div class="metrics-grid">
            <div class="glass-card">
                <div class="metric-title">Total Calls</div>
                <div class="metric-value value-primary" id="val-total">0</div>
            </div>
            <div class="glass-card">
                <div class="metric-title">Success Rate</div>
                <div class="metric-value value-primary" id="val-rate">0%</div>
            </div>
            <div class="glass-card">
                <div class="metric-title">Successful</div>
                <div class="metric-value value-success" id="val-success">0</div>
            </div>
            <div class="glass-card">
                <div class="metric-title">Failed</div>
                <div class="metric-value value-danger" id="val-failed">0</div>
            </div>
        </div>

        <div class="glass-card recent-calls">
            <h2>Recent Call History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Call ID</th>
                        <th>Time (Local)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="calls-tbody">
                    <!-- Populated by JS -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                
                animateValue('val-total', data.total);
                
                const rateEl = document.getElementById('val-rate');
                if (rateEl) rateEl.textContent = data.rate + '%';
                
                animateValue('val-success', data.successful);
                animateValue('val-failed', data.failed);

                const tbody = document.getElementById('calls-tbody');
                tbody.innerHTML = '';
                
                if (data.recent.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 3rem; color:#64748b;">No call data available yet. Waiting for inbound connections...</td></tr>';
                } else {
                    data.recent.forEach(call => {
                        const tr = document.createElement('tr');
                        
                        const idTd = document.createElement('td');
                        idTd.className = 'anon-id';
                        idTd.textContent = call.id.substring(0, 12) + '...';
                        
                        const timeTd = document.createElement('td');
                        const date = new Date(call.time + 'Z'); 
                        timeTd.textContent = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                        timeTd.style.color = '#94a3b8';
                        timeTd.style.fontSize = '0.9rem';
                        
                        const statusTd = document.createElement('td');
                        const badge = document.createElement('span');
                        badge.className = call.status === 'success' ? 'status-badge status-success' : 'status-badge status-failed';
                        badge.textContent = call.status;
                        statusTd.appendChild(badge);
                        
                        tr.appendChild(idTd);
                        tr.appendChild(timeTd);
                        tr.appendChild(statusTd);
                        tbody.appendChild(tr);
                    });
                }
            } catch (err) {
                console.error("Failed to fetch metrics", err);
            }
        }

        function animateValue(id, end) {
            const el = document.getElementById(id);
            if (!el) return;
            const start = parseInt(el.textContent) || 0;
            if (start === end) return;
            el.textContent = end;
        }

        fetchMetrics();
        setInterval(fetchMetrics, 3000);
    </script>
</body>
</html>
"""

class AnalyticsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to keep terminal clean
        pass

    def get_metrics(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
            if not cursor.fetchone():
                return {"total": 0, "successful": 0, "failed": 0, "rate": 0, "recent": [], "unique_callers": 0, "chart_data": [], "distribution": []}
                
            cursor.execute("SELECT COUNT(*) FROM calls")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT caller_id) FROM calls")
            unique_callers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM calls WHERE status='success'")
            successful = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM calls WHERE status='failed'")
            failed = cursor.fetchone()[0]
            
            cursor.execute("SELECT call_id, status, created_at FROM calls ORDER BY created_at DESC LIMIT 10")
            recent_rows = cursor.fetchall()
            recent = [{"id": r[0], "status": r[1], "time": r[2]} for r in recent_rows]
            
            rate = int((successful / total * 100)) if total > 0 else 0
            
            # Chart Data (Last 7 Days)
            cursor.execute("""
                SELECT date(created_at) as d, COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)
                FROM calls 
                WHERE created_at >= date('now', '-6 days')
                GROUP BY d
                ORDER BY d
            """)
            rows = cursor.fetchall()
            from datetime import timedelta, date
            chart_data = []
            today = date.today()
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                d_str = d.strftime('%Y-%m-%d')
                calls_cnt = 0
                success_cnt = 0
                for r in rows:
                    if r[0] == d_str:
                        calls_cnt = r[1]
                        success_cnt = r[2]
                        break
                chart_data.append({
                    "name": d.strftime('%a'), 
                    "calls": calls_cnt,
                    "success": success_cnt
                })
                
            # Distribution Data
            try:
                cursor.execute("SELECT issue_category, COUNT(*) FROM calls GROUP BY issue_category")
                cat_rows = cursor.fetchall()
            except sqlite3.OperationalError:
                cat_rows = []
                
            distribution_map = {
                "Weather Alerts": 0,
                "Hospital Search": 0,
                "Rescue Esc.": 0,
                "General Safety": 0
            }
            for r in cat_rows:
                cat = r[0] if r[0] else "General Safety"
                cnt = r[1]
                if cat in distribution_map:
                    distribution_map[cat] = cnt
                else:
                    distribution_map["General Safety"] += cnt
                    
            distribution = []
            if total > 0:
                for k, v in distribution_map.items():
                    distribution.append({
                        "name": k,
                        "val": int(v / total * 100),
                        "count": v
                    })
            else:
                for k in distribution_map.keys():
                    distribution.append({"name": k, "val": 0, "count": 0})
            
            conn.close()
            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "rate": rate,
                "recent": recent,
                "unique_callers": unique_callers,
                "chart_data": chart_data,
                "distribution": distribution
            }
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return {"total": 0, "successful": 0, "failed": 0, "rate": 0, "recent": [], "unique_callers": 0, "chart_data": [], "distribution": []}

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
            
        elif parsed.path == '/api/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            metrics = self.get_metrics()
            self.wfile.write(json.dumps(metrics).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, AnalyticsHandler)
    print("=" * 50)
    print(f"Call Analytics Dashboard running at:")
    print(f"-> http://localhost:{port}")
    print("=" * 50)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        httpd.server_close()

if __name__ == '__main__':
    run()
