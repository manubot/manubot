from dataclasses import dataclass


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
            raise ValueError(
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
        from manubot.cite.csl_item import CSL_Item
        return CSL_Item()

    def citekey(self):
        from manubot.cite.citekey import CiteKey
        return CiteKey(self.tag)

    @property
    def source(self):
        return self.__class__.__name__.lower()
    
    @property
    def tag(self):
        return f'{self.source}:{self.identifier}'
