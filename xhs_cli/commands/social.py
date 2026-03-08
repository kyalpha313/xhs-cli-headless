"""Social commands: follow, unfollow, user-collects."""

import click

from ..exceptions import NoCookieError, XhsApiError
from ..formatter import print_error, print_info, print_json, print_success
from ._common import get_client as _get_client


@click.command()
@click.argument("user_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def follow(ctx, user_id: str, as_json: bool):
    """Follow a user."""
    try:
        with _get_client(ctx) as client:
            data = client.follow_user(user_id)

        if as_json:
            print_json(data)
        else:
            print_success(f"Followed user {user_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("user_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def unfollow(ctx, user_id: str, as_json: bool):
    """Unfollow a user."""
    try:
        with _get_client(ctx) as client:
            data = client.unfollow_user(user_id)

        if as_json:
            print_json(data)
        else:
            print_success(f"Unfollowed user {user_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("user_id")
@click.option("--cursor", default="", help="Pagination cursor")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def favorites(ctx, user_id: str, cursor: str, as_json: bool):
    """List a user's favorited (bookmarked) notes."""
    try:
        with _get_client(ctx) as client:
            data = client.get_user_favorites(user_id, cursor=cursor)

        if as_json:
            print_json(data)
        else:
            from ..formatter import render_user_posts
            notes = data.get("notes", []) if isinstance(data, dict) else []
            render_user_posts(notes)
            if isinstance(data, dict) and data.get("has_more"):
                print_info(f"More notes — use --cursor {data.get('cursor', '')}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None
