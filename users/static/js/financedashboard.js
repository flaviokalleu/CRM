// Podemos, por exemplo, adicionar uma animação suave quando o saldo for atualizado.
document.addEventListener('DOMContentLoaded', function() {
    let saldoElement = document.querySelector('.numbers');
    let initialSaldo = 0;
    let finalSaldo = parseFloat(saldoElement.textContent.replace('$', ''));
    
    let interval = setInterval(() => {
        if(initialSaldo < finalSaldo) {
            initialSaldo += 10; // incrementar em $10 (pode ajustar conforme necessário)
            saldoElement.textContent = '$' + initialSaldo.toFixed(2);
        } else {
            clearInterval(interval);
        }
    }, 50);
});
