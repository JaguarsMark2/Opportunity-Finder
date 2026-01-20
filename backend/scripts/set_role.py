import sys
from app.db import SessionLocal
from app.models import User, UserRole

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/set_role.py <email> <USER|ADMIN>")
        sys.exit(1)

    email = sys.argv[1].lower().strip()
    role_str = sys.argv[2].upper().strip()

    if role_str not in ("USER", "ADMIN"):
        print("Role must be USER or ADMIN")
        sys.exit(1)

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            print("No such user:", email)
            sys.exit(2)
        u.role = UserRole.ADMIN if role_str == "ADMIN" else UserRole.USER
        db.commit()
        print("OK:", u.email, u.role)
    finally:
        db.close()

if __name__ == "__main__":
    main()
