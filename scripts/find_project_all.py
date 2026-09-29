import os, glob

edge_data = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data')

matches = []
for root, dirs, files in os.walk(edge_data):
    for f in files:
        if f.endswith(('.log', '.ldb', '.txt', '.json', '.bak')):
            path = os.path.join(root, f)
            try:
                with open(path, 'rb') as fp:
                    content = fp.read()
                    if b'rqwpafatgsyncvretjym' in content:
                        print(f'Match in {path} (size: {len(content)})')
                        pos = 0
                        while True:
                            pos = content.find(b'rqwpafatgsyncvretjym', pos)
                            if pos == -1: break
                            snippet = content[max(0, pos-150):min(len(content), pos+350)]
                            print('--- SNIPPET ---')
                            print(repr(snippet))
                            pos += len(b'rqwpafatgsyncvretjym')
            except Exception as e:
                pass
