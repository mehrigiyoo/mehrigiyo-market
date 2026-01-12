# MehrigiyoBackend

### Requirements:
- Python 3.11^ (or newer) (Recommended: 3.12.x)

### Getting started
1. Clone repository:
```shell
git clone https://github.com/Mehrigiyouz/MehrigiyoBackend.git
```

2. Create virtual environment directory
```shell
python -m venv .env
```

3. Activate virtual environment:
```shell
source .env/bin/activate
```

4. Install required dependencies:
```shell
pip install -r requirements.txt
```

5. Create `.env` file:
```shell
touch config/.env
```

Example `.env` file:
```env
SECRET_KEY="django-insecure-ui1d-k7ojs(_etnx33=4jt0y_v@4w2ejv*cxa(mkc4$&_hr4sf"
DEBUG=True
PAYME_ID="62f9e8aea12ad7a48f4b0e33"
PAYME_KEY="fc&qW5zZjp2%KzZ7qwOg@3zxNCuiEab4n%dQ"
DEFAULT_DELIVERY_COST=0
SMS_USERNAME="doctorali"
SMS_PASSWORD="Sy9pqTe!*Q,("
DATABASE_URL="psql://LOGIN:PASSWORD@127.0.0.1/mehrigiyo"
BASE_URL="123.123.12.123"
ANDROID_REG_KEY="dp0ABJ-5TMKoXXynpUmODt:APA91bF09fzm-N8IhiAEnhtGBYdIaACFNJU8Rv8S_1CXmO6Jshb06DZBSwEW-wGbsgD3QbrhwTnmJTakJwC7hU4dCjVwK1JVx7-y9zwXV-d2BBUfVF5y7h88vB9JgT76HUsJYMkF2b0z"
IOS_REG_KEY="f32nsphpl0cenFuo32Z63h:APA91bHmg5Pdlm61H1qPnMNTSYiVi-mJ9SDQjP8MU8RE6XiMwKhsr0-ouq3Ka9Fv-hLrWe6Q4FVuyqEkwxuvxjQaTeaelNAGDu93VUzVZ3TQLEidDCV9EznuB07-O-4VsunuQ5eNvv58"
```

6. Run migrations:
```shell
python manage.py migrate
```

### Development
1. Activate virtual environment:
```shell
source .env/bin/activate
```

2. Start local server:
```shell
python manage.py runserver
```

### Deployment
1. Fetch / Merge commits
```shell
git pull
```

2. Restart web server
```shell
make
```
# Mehrigiyo-Market
# mehrigiyo-market
