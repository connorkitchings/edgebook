"""CLI utility for managing system user roles and user provisioning."""

import argparse
import sys

from edgebook.auth.models import AppUser, UserRole
from edgebook.auth.services import create_user
from edgebook.core.database import SessionLocal


def main() -> None:
    """Run the command line utility for user administration."""
    parser = argparse.ArgumentParser(description="Manage Edgebook users and roles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("username", type=str)
    create_parser.add_argument("password", type=str)
    create_parser.add_argument(
        "--role",
        type=str,
        choices=[r.value for r in UserRole],
        default=UserRole.USER.value,
    )
    create_parser.add_argument("--bankroll-cents", type=int, default=1000000)

    # Promote command
    promote_parser = subparsers.add_parser(
        "promote", help="Promote an existing user to a role"
    )
    promote_parser.add_argument("username", type=str)
    promote_parser.add_argument("role", type=str, choices=[r.value for r in UserRole])

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.command == "create":
            user = create_user(
                db,
                username=args.username,
                password=args.password,
                role=args.role,
                starting_bankroll_cents=args.bankroll_cents,
            )
            print(f"Successfully created user: {user.username} with role: {user.role}")
        elif args.command == "promote":
            username = args.username.strip().lower()
            target_user = db.query(AppUser).filter(AppUser.username == username).first()
            if not target_user:
                print(f"Error: User '{args.username}' not found", file=sys.stderr)
                sys.exit(1)
            target_user.role = args.role
            db.commit()
            print(
                f"Successfully promoted user {target_user.username} "
                f"to role {target_user.role}"
            )
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
