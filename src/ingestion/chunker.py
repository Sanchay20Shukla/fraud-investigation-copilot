import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_chunks(directory):
    """Markdown section citations keep the synthetic policies easy to audit."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    result = []
    for path in sorted(directory.glob('*.md')):
        content = path.read_text(encoding='utf-8')
        section = 'Overview'
        for block in content.split('\n## '):
            if '\n' in block:
                section, body = block.split('\n', 1)
            else:
                body = block
            for index, piece in enumerate(splitter.split_text(body)):
                digest = hashlib.sha256(piece.encode()).hexdigest()
                result.append({'chunk_id': hashlib.sha256(f'{path.name}:{section}:{index}:{digest}'.encode()).hexdigest()[:20],
                    'source': path.name, 'section': section.strip('# '), 'content': piece, 'digest': digest})
    if not result:
        raise ValueError('No policy documents found')
    return result
