from dataclasses import dataclass

class CiteKeyParsingError(ValueError):
    pass


def split_prefixed_identifier(string: str):
    """
    Split strings like 'doi:blah' into source prefix and identifier 
    ('doi', 'blah')
    String must contain a colon (:). Accepts strings starting with '@'.
    Raises error if source prefix not defined.
    """
    string = string.strip()
    trimmed = string[1:] if string.startswith('@') else string
    try:
        source, identifier = trimmed.split(':', 1)
    except ValueError:
        raise CiteKeyParsingError(f"Could not process '{string}' as citekey.")
    source = source.strip().lower()
    identifier = identifier.strip()
    Handle.validate(source)  # raises error on wrong source prefix
    return source, identifier


class CiteKey(object):
    def __init__(self, citekey):
        self.source, self.identifier = split_prefixed_identifier(citekey)

    def handle(self):
        return Handle.create_with(self.source, self.identifier)

    def str(self):
        """Use in chained transformation of citekey as citekey.str()
           Same result as str(citekey)"""
        return str(self)

    def __str__(self):
        return f'{self.source}:{self.identifier}'

    def __repr__(self):
        return "CiteKey(citekey='{}')".format(self)


class HandleBase:
    """
    Parent (grandfather) class for handles like DOI, ISBN and other.

    Public classmethods:
      .source_prefixes() -> [str]
      .validate(source: str)   
      .create_with(source: str, identifier: str)
    """   
    @classmethod
    def _class_dict(cls):
        # Must provide import to all handle classes here too make them 
        # discoverable and avoid a circular import problem.
        from manubot.cite.doi import DOI
        return {c.__name__.lower(): c for c in cls.__subclasses__()}

    @classmethod
    def source_prefixes(cls)  -> [str]:
        return list(cls._class_dict().keys())

    @classmethod
    def _get_constructor(cls, key):
        try:
            return cls._class_dict()[key.lower()]
        except KeyError:
            raise CiteKeyParsingError(
                    f'Prefix {key} not supported.\n'
                    f'Must be one of {cls.source_prefixes()}')

    @classmethod
    def validate(cls, source):
        _ = cls._get_constructor(source)
            
    @classmethod
    def create_with(cls, source: str, identifer: str):
        """
        Create DOI, ISBN and other handles from source name (eg 'doi')
        and identifier (eg '10.1038/d41586-019-02978-7')
        """
        constr = cls._get_constructor(source)
        return constr(identifer)


@dataclass
class Handle(HandleBase):
    """
    Parent class for DOI, ISBN and other supported handles.
    Child class names in lowercase will be treated as source prefixes, eg DOI -> doi.
    """
    identifier: str

    # Child classes may redefine canonic(), otherwise this method just passes 
    # orginal identifer, if not change needed to stadardize the identifer.
    def canonic(self):
        return self

    # Child classes must redefine csl_item() method.
    # This can probably be enforced with @abc.abstractmethod.
    def csl_item(self):
        return CSL_Item()

    def citekey(self):
        return CiteKey(self.tag)

    @property
    def source(self):
        return self.__class__.__name__.lower()
    
    @property
    def tag(self):
        return f'{self.source}:{self.identifier}'


class CSL_Item(dict):
    def __init__(self, incoming_dict: dict = {}):
        super().__init__(incoming_dict)

    def set_id(self, x):
        self['id'] = x
        return self

    @staticmethod
    def add_note(x):
        return x

    @staticmethod
    def generate_id(x):
        """If item has no id, make a hash"""
        return x

    @staticmethod
    def fix_type(x):
        return x

    @staticmethod
    def prune(self, x):
        return x

    def minimal(self):
        keys = ('title author URL issued type container-title'
                'volume issue page DOI').split()
        return CSL_Item({k: v for k, v in self.items() if k in keys})

    def clean(self, prune=True):
        csl_item = self
        # csl_item.fix_type()
        # csl_item.add_note()
        # csl_item.generate_id()
        # if prune:
        #    csl_item.prune()
        return csl_item

