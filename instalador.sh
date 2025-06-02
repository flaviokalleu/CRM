#!/bin/bash

# Função para exibir mensagens informativas
informar() {
    clear
    echo "======================================="
    echo "| CRIADO CRM FLAVIO KALLEU - $1"
    echo "======================================="
    sleep 2
}

# Função para exibir mensagens de erro
erro() {
    echo "Erro: $1"
    exit 1
}

# Atualizar o sistema
informar "Atualizando o sistema..."
sudo apt update || erro "Falha ao atualizar o sistema"
sudo apt upgrade -y || erro "Falha ao atualizar o sistema"
clear

# Instalar pacotes essenciais para compilação
informar "Instalando pacotes essenciais para compilação..."
sudo apt install -y build-essential python3-dev || erro "Falha ao instalar pacotes essenciais para compilação"
clear

# Instalar o MySQL
informar "Instalando o MySQL..."
sudo apt install mysql-server -y || erro "Falha ao instalar o MySQL"
clear

# Instalar o libmysqlclient-dev
informar "Instalando o libmysqlclient-dev..."
sudo apt install libmysqlclient-dev -y || erro "Falha ao instalar o libmysqlclient-dev"
clear

# Configurar o MySQL e criar o usuário crm
informar "Configurando o MySQL e criando o usuário crm..."
sudo mysql -e "CREATE USER 'crm'@'localhost' IDENTIFIED BY '99480231aA!';" || erro "Falha ao criar o usuário crm"
sudo mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'crm'@'localhost';" || erro "Falha ao conceder privilégios ao usuário crm"
sudo mysql -e "FLUSH PRIVILEGES;" || erro "Falha ao atualizar os privilégios do MySQL"
clear

# Instalar o Python 3.9 usando o PPA deadsnakes
informar "Instalando Python 3.9 usando o PPA deadsnakes..."
sudo add-apt-repository ppa:deadsnakes/ppa -y || erro "Falha ao adicionar o repositório PPA"
sudo apt update || erro "Falha ao atualizar o sistema"
sudo apt install python3.9 -y || erro "Falha ao instalar Python 3.9"
clear

# Verificar se o Python 3.9 foi instalado corretamente
python3.9 --version || erro "Falha ao verificar a instalação do Python 3.9"
clear

# Instalar pip
informar "Instalando pip..."
sudo apt install python3-pip -y || erro "Falha ao instalar o pip"
clear

# Instalar mysqlclient
informar "Instalando mysqlclient..."
pip install mysqlclient || erro "Falha ao instalar mysqlclient"
clear


# Instalar Node.js (versão 16.x)
informar "Instalando Node.js (versão 16.x)..."
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash - || erro "Falha ao adicionar o repositório do Node.js"
sudo apt-get install -y nodejs || erro "Falha ao instalar Node.js"
clear

# Instalar o zip
informar "Instalando zip..."
sudo apt install zip -y || erro "Falha ao instalar o zip"
clear

# Extrair os arquivos do crm.zip para a pasta crm
informar "Extraindo arquivos do crm.zip..."
mkdir -p crm || erro "Falha ao criar o diretório 'crm'"
unzip -q crm.zip -d crm || erro "Falha ao extrair arquivos do crm.zip"
clear

# Entrar na pasta crm
cd crm || erro "Falha ao entrar no diretório 'crm'"

# Instalar as dependências do Python a partir do requirements.txt
informar "Instalando todas as dependências..."
pip install amqp asgiref async-timeout attrs beautifulsoup4 billiard celery certifi cffi charset-normalizer chromedriver-autoinstaller click click-didyoumean click-plugins click-repl colorama cryptography Django django-appconf django-extensions django-multiupload django-select2 django-widget-tweaks djangorestframework emoji exceptiongroup h11 idna kombu mysqlclient outcome packaging pdfminer.six pdfplumber Pillow prompt-toolkit pycparser PyMuPDF PyMuPDFb pypdf2 pypdfium2 PySocks python-dateutil python-decouple python-dotenv pytz redis reportlab requests selenium six sniffio sortedcontainers soupsieve sqlparse trio trio-websocket typing-extensions tzdata urllib3 vine wcwidth webdriver-manager wget whitenoise wsproto
clear

informar "Instalando dependências do Node.js..."
npm install || erro "Falha ao instalar as dependências do Node.js"
clear

# Configurar o Nginx para servir arquivos estáticos do Django
informar "Configurando Nginx para servir arquivos estáticos do Django..."
sudo bash -c 'cat > /etc/nginx/sites-available/3brokers.com.br << EOF
server {
    listen 80;
    server_name 3brokers.com.br;

    location /static/ {
        alias $(pwd)/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF' || erro "Falha ao configurar o Nginx"
clear

# Criar link simbólico para o arquivo de configuração do Nginx
sudo ln -s /etc/nginx/sites-available/3brokers.com.br /etc/nginx/sites-enabled/ || erro "Falha ao criar link simbólico"
clear

# Reiniciar o Nginx para aplicar as alterações
sudo systemctl restart nginx || erro "Falha ao reiniciar o Nginx"
clear
informar "Realizando o makemigrations no Django..."
python3.9 manage.py makemigrations || erro "Falha ao realizar o migrate no Django"
clear
# Realizar o migrate no Django
informar "Realizando o migrate no Django..."
python3.9 manage.py migrate || erro "Falha ao realizar o migrate no Django"
clear

# Iniciar o servidor Node.js
informar "Iniciando o servidor Node.js..."
node serve.js || erro "Falha ao iniciar o servidor Node.js"
clear

# Iniciar o Django na porta 8000
informar "Iniciando Django na porta 8000..."
python3.9 manage.py runserver 0.0.0.0:8000 || erro "Falha ao iniciar o Django na porta 8000"
clear

# Limpar a tela
clear
