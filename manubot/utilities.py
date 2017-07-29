import hashlib

import base62


def get_citation_id(standard_citation, digest_size=6):
    """
    Get the citation_id for a standard_citation.
    """
    as_bytes = standard_citation.encode()
    blake_hash = hashlib.blake2b(as_bytes, digest_size=digest_size)
    digest = blake_hash.digest()
    citation_id = base62.encodebytes(digest)
    return citation_id
