from kay.conf import settings

def gfc_settings(request):
  return {'gfc_site_id': settings.GFC_SITE_ID}