import re
import os
import base64
import fitz  # PyMuPDF
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CONVENIO, USERNAME, PASSWORD
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller


def remove_phrases_from_pdf(pdf_file, output_file):
    doc = fitz.open(pdf_file)

    # Define as frases a serem removidas
    phrases_to_remove = [
        "Código do Correspondente: 000703230",
        "Código do Convênio 00070323-0 Identificação do Operador Flavio"
    ]

    for page_num in range(doc.page_count):
        page = doc[page_num]

        # Redaciona o texto das frases especificadas
        for phrase in phrases_to_remove:
            rects = page.search_for(phrase)
            for rect in rects:
                annot = page.add_redact_annot(rect)

        # Aplica as redações
        page.apply_redactions()
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    # Salva o novo arquivo PDF
    doc.save(output_file)
    doc.close()


def consulta_cpf_func(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)

    

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_experimental_option('prefs', {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    # Configuração do proxy usando o IP do usuário (se necessário)

    # Inicia o Selenium
    print("Iniciando o Selenium...")

    # Instala o ChromeDriver automaticamente
    chromedriver_autoinstaller.install()

    # Inicializa o WebDriver usando o ChromeDriver gerenciado pelo webdriver_manager
    browser = webdriver.Chrome(options=chrome_options)

    print("Selenium iniciado!")

    browser.get('https://caixaaqui.caixa.gov.br/caixaaqui/CaixaAquiController')

    browser.get(
        'https://caixaaqui.caixa.gov.br/caixaaqui/CaixaAquiController')

    convenio_input = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#convenio'))
    )
    convenio_input.send_keys(CONVENIO)

    login_input = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#login'))
    )
    login_input.send_keys(USERNAME)

    password_input = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#password'))
    )
    password_input.send_keys(PASSWORD)

    submit_button = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.btn-azul'))
    )
    submit_button.click()

    elements_to_click = [
        '/html/body/div/div[1]/div[2]/form/center/table[2]/tbody/tr[1]/td/a',
        '/html/body/center/table[2]/tbody/tr[1]/td/a',
        '/html/body/center/form/table[1]/tbody/tr[1]/td/a'
    ]

    for element_xpath in elements_to_click:
        element = WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.XPATH, element_xpath))
        )
        element.click()

    cpf_input = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/form/center/div[2]/div[2]/table/tbody/tr[3]/td/div[1]/input'))
    )
    cpf_input.send_keys(cpf)

    submit_button = WebDriverWait(browser, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#spanCPF .btn-azul'))
    )
    submit_button.click()

    directory = 'static/uploads/PDF'

    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = os.path.join(directory, f"{cpf}.pdf")

    # Verifica se o arquivo já existe
    if os.path.exists(filename):
        # Atualiza o arquivo existente
        pdf_content = browser.execute_cdp_cmd("Page.printToPDF", {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
        })

        with open(filename, 'wb') as f:
            f.write(base64.b64decode(pdf_content['data']))
    else:
        # Cria um novo arquivo
        pdf_content = browser.execute_cdp_cmd("Page.printToPDF", {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
        })

        with open(filename, 'wb') as f:
            f.write(base64.b64decode(pdf_content['data']))

        output_filename = os.path.join(directory, f"{cpf}_modified.pdf")
        remove_phrases_from_pdf(filename, output_filename)

    browser.quit()

    file_url = f"static/uploads/PDF/{cpf}_modified.pdf"
    return {"message": "Consulta concluída com sucesso.", "file_url": file_url}
