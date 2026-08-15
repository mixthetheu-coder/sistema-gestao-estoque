import time
import requests
import schedule

# ==========================================
# CONFIGURAÇÕES DE CREDENCIAIS (Preencha aqui)
# ==========================================
TELEGRAM_TOKEN =  "SEU_TOKEN_AQUI"  # Cole o Token do BotFather
CHAT_ID = "SEU_CHAT_ID_AQUI"  # Cole o ID do userinfobot

# Banco de dados/lista simulada de estoque
estoque = {
    "Arroz 5kg": 12,
    "Feijão 1kg": 3,  # Estoque baixo
    "Óleo de Soja": 2,  # Estoque baixo
    "Açúcar 1kg": 15,
}


def enviar_alerta_telegram(mensagem):
    """Envia a mensagem formatada para o chat do Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}

    try:
        resposta = requests.post(url, json=payload)
        if resposta.status_code == 200:
            print("✅ Alerta enviado com sucesso no Telegram!")
        else:
            print(
                f"❌ Erro ao enviar: {resposta.status_code} - {resposta.text}"
            )
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")


def verificar_estoque_critico(limite=5):
    """Varre o estoque e identifica produtos com quantidade abaixo do limite."""
    produtos_criticos = []
    for item, qtd in estoque.items():
        if qtd < limite:
            produtos_criticos.append(
                f"⚠️ *{item}*: apenas {qtd} unidades no estoque!"
            )

    if produtos_criticos:
        relatorio = (
            "🚨 *ALERTA DE REPOSIÇÃO DE ESTOQUE*\n\n"
            + "\n".join(produtos_criticos)
        )
        enviar_alerta_telegram(relatorio)
    else:
        print("Estoque normal. Nenhum alerta disparado.")


def tarefa_agendada():
    print(f"\n[{time.strftime('%H:%M:%S')}] Executando verificação de estoque...")
    verificar_estoque_critico()


# ==========================================
# AGENDAMENTO DAS TAREFAS
# ==========================================

# Opção 1: Rodar todos os dias às 08:00 (ideal para produção/clientes)
schedule.every().day.at("08:00").do(tarefa_agendada)

# Opção 2: Rodar a cada 1 minuto (ideal para você TESTAR agora)
# Descomente a linha abaixo para testar a cada minuto:
# schedule.every(1).minutes.do(tarefa_agendada)

if __name__ == "__main__":
    print("🤖 Bot de automação de estoque iniciado!")
    print("Aguardando horário programado para verificação...\n")

    # Executa uma vez imediatamente ao iniciar para testar
    tarefa_agendada()

    # Loop contínuo mantendo o script ativo
    while True:
        schedule.run_pending()
        time.sleep(1)

