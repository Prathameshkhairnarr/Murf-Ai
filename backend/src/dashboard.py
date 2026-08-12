import sqlite3
import time
import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "callers.db")
    
    while True:
        clear_screen()
        print("=" * 70)
        print(" 🚨 NDRF HUMAN RESCUE DISPATCH DASHBOARD 🚨 ".center(70))
        print("=" * 70)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT reference_id, caller_name, caller_id, urgency, summary, status, created_at 
                FROM escalations 
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            
            if not rows:
                print("\n  [✓] No active emergency escalations. All areas clear.\n")
            else:
                for row in rows:
                    ref, name, phone, urgency, summary, status, created = row
                    
                    # Icons based on urgency
                    icon = "🟢"
                    if urgency == "emergency": icon = "🔴"
                    elif urgency == "high": icon = "🟠"
                    elif urgency == "medium": icon = "🟡"
                    
                    print(f"\n{icon} [{ref}] | URGENCY: {urgency.upper()} | STATUS: {status.upper()}")
                    print(f"    👤 Caller: {name} ({phone})")
                    print(f"    🕒 Time:   {created}")
                    print(f"    📝 Report: {summary}")
                    print("-" * 70)
                    
            conn.close()
        except sqlite3.OperationalError:
            print("\n  [!] Database not found or escalations table missing. Waiting...\n")
            
        print("\n(Auto-refreshing every 3 seconds. Press Ctrl+C to exit)")
        time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting dashboard...")
        sys.exit(0)
