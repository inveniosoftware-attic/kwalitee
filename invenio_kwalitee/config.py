COMPONENTS = [
    'base',
    'celery',
    'global',
    'grunt',
    'installation',
    'utils',
    # modules
    'access',
    'accounts',
    'alerts',
    'apikeys',
    'authorids',
    'authorprofiles',
    'baskets',
    'bulletin',
    'circulation',
    'classifier',
    'cloudconnector',
    'comments',
    'communities',
    'converter',
    'dashboard',
    'deposit',
    'documentation',
    'documents',
    'editor',
    'encoder',
    'export',
    'exporter',
    'formatter',
    'groups',
    'indexer',
    'jsonalchemy',
    'knowledge',
    'linkbacks',
    'matcher',
    'merger',
    'messages',
    'oaiharvester',
    'oairepository',
    'pidstore',
    'previewer',
    'previews',
    'ranker',
    'record_editor',
    'records',
    'redirector',
    'refextract',
    'scheduler',
    'search',
    'sequencegenerator',
    'sorter',
    'statistics',
    'submit',
    'sword',
    'tags',
    'textminer',
    'tickets',
    'upgrader',
    'uploader',
    'workflows',
]

SIGNATURES = 'Signed-off-by', 'Tested-by', 'Reviewed-by'

TRUSTED_DEVELOPERS = []

REPO_URL = 'https://github.com/inveniosoftware/invenio/'

PEP8_IGNORE = 'E123', 'E226', 'E24', 'E501', 'E265'
#PEP8_SELECT = 'E111', 'F481'

CHECK_WIP = False
CHECK_COMMIT_MESSAGES = True
CHECK_PEP8 = True
# PyFlakes requires PEP8
CHECK_PYFLAKES = True
