import dropbox
from django.conf import settings
from dropbox.files import WriteMode


def get_dropbox_client():
    return dropbox.Dropbox(
        oauth2_refresh_token=settings.DROPBOX_REFRESH_TOKEN,
        app_key=settings.DROPBOX_APP_KEY,
        app_secret=settings.DROPBOX_APP_SECRET,
    )


def upload_to_dropbox(file_obj, order_number, filename):
    """Upload a file to /Customer Uploads/Builders Signs/<order_number>/<filename>
    and return (path, shared_url)."""
    dbx = get_dropbox_client()
    path = f"/Customer Uploads/Builders Signs/{order_number}/{filename}"
    result = dbx.files_upload(file_obj.read(), path, mode=WriteMode.add, autorename=True)
    actual_path = result.path_display
    try:
        link = dbx.sharing_create_shared_link_with_settings(actual_path)
        shared_url = link.url
    except Exception:
        try:
            links = dbx.sharing_list_shared_links(path=actual_path, direct_only=True)
            shared_url = links.links[0].url if links.links else ''
        except Exception:
            shared_url = ''
    return actual_path, shared_url
