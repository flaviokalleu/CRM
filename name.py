import os

def corrigir_nomes(diretorio):
    # Percorre todos os arquivos e pastas no diretório
    for pasta_atual, sub_pastas, arquivos in os.walk(diretorio):
        # Lista de pastas que devem ter a primeira letra em minúscula
        pastas_a_corrigir = ['Documentos_conjuge', 'Documentos_dependente', 'Documentos_pessoais', 'Extrato_bancario']

        # Renomeia a pasta atual, se estiver na lista
        pasta_atual_nome = os.path.basename(pasta_atual)
        if pasta_atual_nome in pastas_a_corrigir and pasta_atual_nome[0].isupper():
            nova_pasta = os.path.join(os.path.dirname(pasta_atual), pasta_atual_nome.lower())
            # Verifica se a pasta existe antes de tentar renomear
            if os.path.exists(pasta_atual):
                os.rename(pasta_atual, nova_pasta)
                print(f"Pasta renomeada: {pasta_atual} -> {nova_pasta}")

        # Percorre os arquivos na pasta
        for nome_arquivo in arquivos:
            # Verifica se o arquivo é um PDF e a primeira letra é maiúscula
            if nome_arquivo.lower().endswith('.pdf') and nome_arquivo[0].isupper():
                # Corrige para minúscula
                novo_nome = nome_arquivo[0].lower() + nome_arquivo[1:]
                
                # Cria o caminho completo dos arquivos antigo e novo
                caminho_antigo = os.path.join(pasta_atual, nome_arquivo)
                caminho_novo = os.path.join(pasta_atual, novo_nome)
                
                # Verifica se o arquivo existe antes de tentar renomear
                if os.path.exists(caminho_antigo):
                    os.rename(caminho_antigo, caminho_novo)
                    print(f"Arquivo renomeado: {caminho_antigo} -> {caminho_novo}")

# Substitua '/root/crm/media/documentos/' pelo caminho do seu diretório
caminho_do_diretorio = '/root/crm/media/documentos/'
corrigir_nomes(caminho_do_diretorio)
