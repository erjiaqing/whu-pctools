import requests, time, hashlib, os, string, random

masterkey = '0123456789abcdef'

def id_generator(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get(ty=False, key=None):
    m = hashlib.sha256()
    m.update((str(int(time.time())) + ':' + masterkey).encode())
    auth = m.hexdigest()
    if not ty:
        return 'http://acm.whu.edu.cn:5000/admin/{}/{}/fetch.json'.format(auth, int(time.time()))
    else:
        return 'http://acm.whu.edu.cn:5000/admin/{}/{}/{}/update.json'.format(auth, int(time.time()), key)


def generate_tex(codename, teamname):
    return r'''
\documentclass[landscape, twocolumn, 10pt]{article}
\usepackage[landscape]{geometry}
\geometry{left=1.5cm,right=1cm,top=2cm,bottom=2cm}
\usepackage{zhfontcfg}
\usepackage{minted}
\usepackage{multirow}
\usepackage{xcolor}
\usepackage{lastpage}
\usepackage{flushend,cuted}
\usepackage{fancyhdr}
\pagestyle{fancy}
\usepackage{mdframed}
\headwidth=\textwidth
\lhead{{\textsc{XXXX Programming Contest}}}
\chead{}
\rhead{Page \thepage of \pageref{LastPage}}
\lfoot{}
\cfoot{}
\rfoot{%s}
\usemintedstyle{bw}
\newmintedfile{text}{tabsize=2,breaklines,fontsize=\small,numbers=left,frame=none}
\setlength{\columnsep}{1cm}
\usepackage{titlesec}
\titlespacing*{\section} {0pt}{0.2cm}{0pt}
\titlespacing*{\subsection} {0pt}{0.1cm}{0pt}
\begin{document}
\textfile{%s}
\end{document}
''' % (teamname, codename)


conn = requests.Session()

while True:
    url = get()
    re = conn.get(url).json()
    if (re.get('result', 'fail') == 'success'):
        print('get new task: user={} taskid={}'.format(re['data'].get('user', ''), re['data'].get('uid', '00000000')[0:7]))
        fname = id_generator(7)
        code = fname + '.txt'
        tex = fname + '.tex'
        fi = open(code, 'wb')
        fi.write(re['data']['content'].encode('utf-8'))
        fi.close()
        wi = open(tex, 'wb')
        wi.write(generate_tex(code,
            r"Team {} ({}) / Task {} / Time {}".format(re['data'].get('user', ''), re['user'].get('note', ''),
                                                           '{\\texttt{' + re['data'].get('uid', '00000000')[0:7] + '}}', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))).encode('utf-8'))
        wi.close()
        os.system('/usr/local/texlive/2016/bin/x86_64-darwin/xelatex --shell-escape -interaction=batchmode {}.tex > /dev/null 2> /dev/null'.format(fname))
        os.system('/usr/local/texlive/2016/bin/x86_64-darwin/xelatex --shell-escape -interaction=batchmode {}.tex > /dev/null 2> /dev/null'.format(fname))
        os.system('lp -d Samsung_M262x_282x_Series -o orientation-requested=4 {}.pdf'.format(fname))
        os.system('mv {} ./static/pdf/{}.pdf'.format(fname + '.pdf', re['data']['uid']))
        os.system('rm {}.*'.format(fname))
        os.system('rm -rf _minted-{}'.format(fname))
        time.sleep(3)
        url = get(True, re['data']['printkey'])
        conn.get(url).json()
        print('Finished ／ Team {}'.format(re['data'].get('user', '')))
    else:
        print('no new tasks')
    time.sleep(3)
