"""Document storage utilities - uses shared DocumentStorage from lexiclass_core."""

import lexiclass_core
from lexiclass_core.storage import DocumentStorage

from .config import settings

# Create a singleton instance configured with API's storage path
document_storage = DocumentStorage(settings.STORAGE_PATH)

# Configure lexiclass_core to use this instance
lexiclass_core.configure_document_storage(document_storage)
