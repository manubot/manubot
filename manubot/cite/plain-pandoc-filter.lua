-- Pandoc lua-filter to change all Emph and Strong elements into plain text
-- https://github.com/jgm/pandoc/issues/4834#issuecomment-412972008
function Emph(el)
  return el.c
end
function Strong(el)
  return el.c
end
