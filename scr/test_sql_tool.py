from db.sql_tool import (
    get_ticket,
    get_customer_recent_orders,
    get_customer_ticket_stats,
    similar_tickets_by_keywords,
    ticket_dashboard_top_categories,
)

def main():
    tid = 1
    t = get_ticket(tid)
    print("\nTICKET:")
    for k in ["id", "subject", "status", "priority", "category", "created_at", "customer_name", "customer_email", "customer_tier"]:
        print(f"  {k}: {t.get(k)}")

    cid = t.get("customer_id")
    if cid:
        print("\nCUSTOMER STATS:")
        print(get_customer_ticket_stats(cid))

        print("\nRECENT ORDERS:")
        for o in get_customer_recent_orders(cid, n=5):
            print(" ", o)

    print("\nSIMILAR TICKETS (keyword LIKE):")
    for s in similar_tickets_by_keywords(tid, k=5):
        print(" ", s["id"], s.get("category"), s.get("priority"), s["preview"])

    print("\nDASHBOARD TOP CATEGORIES:")
    for r in ticket_dashboard_top_categories(limit=10):
        print(" ", r)

if __name__ == "__main__":
    main()
