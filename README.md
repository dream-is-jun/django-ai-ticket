# AI 智能工单管理系统

基于 Django、Django REST Framework 和通义千问开发的智能工单系统。

## 功能

- 用户注册、登录和退出
- 工单增删改查
- 用户数据权限隔离
- 客服回复和状态流转
- 工单搜索、筛选和分页
- 通义千问自动摘要、分类、优先级判断
- AI 客服建议回复
- REST API
- 自动化测试
- 数据统计看板

## 技术栈

- Python
- Django
- Django REST Framework
- SQLite / PostgreSQL
- Qwen-Plus
- OpenAI Compatible API
- Bootstrap

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver