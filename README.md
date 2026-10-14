# 2026 软件工程课程设计 · 知课课程注册系统

Vue + Flask + PostgreSQL 的完整课程注册演示项目。五人小组：陈辰（组长）、董宇曦、刘根森、李怡宁、赵毓豪。

## 启动

在 `02-源代码` 目录执行：

```bash
docker compose up -d --build
```

打开 **http://127.0.0.1:8080**。首次构建需下载 Python 依赖和基础镜像。包内已有 Vue 生产构建产物，演示启动不需要 Node。PostgreSQL 18 使用命名卷持久化，已有数据库不会被初始化脚本覆盖。

```bash
docker compose ps
docker compose logs --tail=80 api worker
docker compose down
```

`down` 停止本项目容器但保留数据。**`down -v` 会删除本项目数据库及模拟计费记录**，只在明确需要重新初始化演示数据时使用。不会操作其他 Docker 项目。

端口冲突时复制 `.env.example` 为 `.env`，修改 `WEB_PORT` / `DB_PORT`。默认网页端口 8080，PostgreSQL 端口 55432，均仅绑定本机。`.env` 的示例密码仅用于演示；数据库卷已存在时，改环境变量不会自动修改数据库内部密码。

## 团队说明

登录卡片下方的“团队说明”可进入 `/#team`，无需登录。页面列明 陈辰、董宇曦、刘根森、李怡宁、赵毓豪 的功能职责与文档产出；计划时间线覆盖 2026 年 9 月 20 日至 10 月 13 日，分为需求与分工、系统设计、核心功能开发、联调与交付准备、运行检查与提交五个阶段。各阶段展示起止日期和交付节点，点击可查看负责人、阶段产出和验收条件。桌面横向展示，手机纵向展示；时间线表示计划安排，实际贡献由成员确认。

## 演示账号

所有初始账号密码均为 `Demo2026!`，登录页按钮可以填入各类默认账号。

| 身份 | 账号 | 用途 |
|---|---|---|
| 教务管理员 | admin | 师生维护、授课资格、关闭选课、计费、操作日志 |
| 教师 | professor01～professor03 | 授课选择、本人名单、上一学期成绩 |
| 学生 | student01～student14 | 选课、草稿、课表、成绩查询 |

student01～student12 有程序设计基础的先修成绩；student13、student14 没有，可用于演示先修校验。student02～student04 初始已选 4 门课程。当前演示环境中 student01 还保留了浏览器验证时提交的 4 门主选和 2 门备选，其程序设计基础成绩被演示修改为 B；全新数据库的 student01 起始没有本学期课表，历史成绩为 A。

## 主要操作

1. **学生**：选择主选“数据结构 02 班、计算机组成原理、数据库原理、软件工程”，备选“计算机网络、操作系统”，首次提交需 4+2。提交成功后有 4 门、13 学分。备选不占名额。可进入“我的课表”查看。
2. **冲突场景**：数据结构 11 班与组成原理 03 班冲突。主选“算法设计与分析”需要先通过数据结构，初始学生均无这项先修成绩。
3. **教师**：professor01 在“名单与成绩”中选择上一学期“程序设计基础 101 班”，可录入 A/B/C/D/F/I。留空不会清除已录入成绩。本学期班级只能查看名单。
4. **教务**：可以维护师生、授课资格；有当前学期课表或授课关联的人员不能直接删除。
5. **关闭选课**：建议最后演示。在“选课管理”确认后，取消无教师及最终不足 3 人的教学班，尝试备选补位，按最终课表产生计费记录。关闭后没有重新开放入口。
6. **计费重试**：关闭前在“外部服务”取消“计费服务可用”，保存，然后关闭选课。在“计费记录”观察 pending，再恢复服务，worker 会自动重试，最长退避间隔 60 秒，页面每 15 秒刷新。
7. **目录故障**：关闭目录可用开关后，缓存最多有效 5 秒；到期后再查目录会显示不可用。恢复开关后可重试。

旧课程目录和计费是独立 HTTP 模拟服务，没有向真实财务系统发送任何信息。本学期状态保留在数据库，不自动按日历变化；“开放期”即管理员关闭前的期间。

## 目录与提交清单

- `01-提交文档/`：封面、开发计划、需求分析、设计、测试计划、测试报告、配置管理计划、小组总结和 5 份个人总结，共 13 个 Word 文件。
- `02-源代码/backend/`：Flask 源码、数据库模型、结构 SQL、数据初始化、重试任务、模拟服务和自动化测试。
- `02-源代码/frontend/`：Vue 源码、Vite 配置及 npm 锁文件。
- `02-源代码/backend/static/`：已构建网页，支持直接 Docker 启动。
- `03-测试证据/`：原始测试日志、JUnit XML、构建记录和界面截图。
- `04-原始要求/`：未修改的课程 PPT、题目 PDF 和封面模板。
- `tools/`：测试、备份及文档生成工具。

交付包附有 `文件校验SHA256.txt`。从项目根目录执行 `python3 tools/package.py` 可重新生成清单和压缩包，自动排除缓存、依赖安装目录、数据库备份与私有 `.env`。文档可直接用 Word 编辑；`generate_docs.py` 依赖 python-docx 和 lxml，仅用于生成基础草稿；现有文档包含成员修订，默认禁止覆盖。显式使用 `--overwrite` 会丢弃后续人工修订。`render_docs.py` 是本机 Codex 排版检查工具，使用本机运行时和字体配置，换电脑时需调整路径，不影响程序启动。

## 界面调整

课程目录和计费列表不显示价格或金额；移除宣传标语、欢迎横幅与重复说明，仅保留选课规则、先修要求、操作反馈及重要确认提示。题目要求的后台计费通知与重试逻辑仍保留。

## 本地开发

只启动数据库和模拟服务，Flask/Vue 在本机调试：

```bash
# 在 02-源代码 下
# mock 默认仅在容器内可见，开发模式使用提供的覆盖文件暴露到本机。
docker compose -f compose.yaml -f compose.dev.yaml up -d db mock init
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
export DATABASE_URL='postgresql+psycopg://course:course_demo_db_2026@127.0.0.1:55432/course'
export CATALOG_URL='http://127.0.0.1:6000'
export BILLING_URL='http://127.0.0.1:6000'
flask --app app:create_app run --port 5000
```

另开终端：

```bash
cd 02-源代码/frontend
npm ci
npm run dev
```

访问 Vite 输出的网址，`/api` 代理到本地 Flask。若需要本地计费任务，在相同环境变量下运行 `python worker.py`。本地开发和容器 API 不要同时改动同一演示库；开始开发前可先停止 `api worker`。

修改 Vue 后构建：

```bash
cd 02-源代码/frontend
npm ci
npm run build
# 产物写入 ../backend/static
cd ..
docker compose up -d --build
```

## 验证

从项目根目录执行：

```bash
bash tools/run-tests.sh
```

只重建独立 `course_test` 库中的表，不影响演示库。当前通过 34 项自动化用例，包括 PostgreSQL 最后名额并发争抢。真实 HTTP 故障联调脚本为 `backend/check_integrations.py`，运行时必须设置独立 mock 地址 `ISOLATED_MOCK_URL`；现有结果保存在测试证据目录。

## 备份

```bash
bash tools/backup.sh
```

备份输出到 `backups/`，包含当前业务数据。恢复前停止 API 和 worker 并核实目标；备份含清理原对象的语句，会覆盖目标数据库内容。真实环境不要使用演示密码，应配置 HTTPS 与正式密钥。

## 资料依据

课程要求及题目位于 `04-原始要求`。实现参考 [Flask 安全文档](https://flask.palletsprojects.com/en/stable/web-security/)、[SQLAlchemy 会话文档](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)、[Vue 快速开始](https://vuejs.org/guide/quick-start)、[PostgreSQL 锁机制](https://www.postgresql.org/docs/current/explicit-locking.html) 和 [Docker PostgreSQL 数据持久化说明](https://docs.docker.com/guides/postgresql/immediate-setup-and-data-persistence/)。
