# blue prints are imported 
# explicitly instead of using *
from .user import user_views
from .index import index_views
from .auth import auth_views
#from .admin import setup_admin
#from .position import position_views
#from .shortlist import shortlist_views
from .applications_api import applications_api
from .applications_api import api
from .application_extras_api import application_extras_api
from .application_extras_api import application_extras_api
from .application_extras_api import openings_extras_api

views = [user_views, index_views, auth_views, applications_api, application_extras_api, openings_extras_api, api] 
# blueprints must be added to this list