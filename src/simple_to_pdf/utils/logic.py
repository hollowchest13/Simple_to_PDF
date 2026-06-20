class InvalidPageInputError(ValueError):
    """Wrong page format"""

class PageLimitExceededError(ValueError):
    """Total page selection exceeds limit."""
    def __init__(self,limit:int):
        super().__init__(f"Total page selection exceeds {limit!r} limit.")
  
def get_selected_pages(*, raw: str,page_limit) -> list[int]:
    pages: set[int] = set() 
    parts = raw.replace(" ", "").split(",")
    for part in parts:
        if not part: continue
        
        if "-" in part:
            s, e = parse_part(part)
            if abs(s - e) > page_limit:
                raise PageLimitExceededError(limit=page_limit)
            pages.update(range(s, e + 1))
        else:
            pages.add(int(part))
        if len(pages) > page_limit:
            raise PageLimitExceededError(limit=page_limit)
    return sorted(list(pages))

def parse_part(part:str)->tuple[int,int]:
    split_char:str="-"
    if split_char in part:
        sides=part.split(split_char)
        if len(sides)!=2 or not all(s.isdigit() for s in sides):
            raise InvalidPageInputError(f"Wrong range{part!r}")
        sides=tuple(map(int,sides))
        s,e=min(sides),max(sides)
        if any(s==0 for s in sides):
            raise InvalidPageInputError("Page numbers can`t be 0")
        return s,e 
    else:
        if not part.isdigit():
            raise InvalidPageInputError(f"Expecting a numeric value:{part!r}")
        p=int(part)
        if p==0:
            raise InvalidPageInputError("Page number can`t be 0")
        return p,p


      


    
