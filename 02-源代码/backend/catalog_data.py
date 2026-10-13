"""Fixed catalog fixture standing in for the legacy Ingres read-only database."""
COURSES = [
    (1,'CS101','程序设计基础',3,90000,None),
    (2,'CS201','数据结构',4,120000,1),
    (3,'CS202','计算机组成原理',3,90000,None),
    (4,'CS203','数据库原理',3,90000,None),
    (5,'CS204','软件工程',3,90000,None),
    (6,'CS205','计算机网络',3,90000,None),
    (7,'CS206','操作系统',4,120000,1),
    (8,'CS207','人工智能导论',2,60000,None),
    (9,'CS208','Web 应用开发',2,60000,None),
    (10,'CS301','算法设计与分析',3,90000,2),
]

def catalog():
    return [dict(id=i,code=c,name=n,credits=cr,fee_cents=f,prerequisite_id=p,department='计算机科学与技术')
            for i,c,n,cr,f,p in COURSES]
