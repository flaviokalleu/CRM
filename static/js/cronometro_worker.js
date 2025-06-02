let miliNum = 0;
let segNum = 0;
let minNum = 0;
let INTERVALO;

self.onmessage = function (event) {
    const action = event.data.action;

    if (action === 'iniciar') {
        iniciar();
    } else if (action === 'parar') {
        parar();
    } else if (action === 'resetar') {
        resetar();
    }
};

function milissegundos() {
    miliNum++;
    if (miliNum === 99) {
        miliNum = 0;
        segundos();
    }
}

function segundos() {
    segNum++;
    if (segNum === 59) {
        segNum = 0;
        minutos();
    }
}

function minutos() {
    minNum++;
}

function iniciar() {
    clearInterval(INTERVALO);
    INTERVALO = setInterval(() => {
        milissegundos();
        postMessage({
            action: 'atualizar',
            minutos: minNum < 10 ? '0' + minNum : minNum,
            segundos: segNum < 10 ? '0' + segNum : segNum,
            milissegundos: miliNum < 10 ? '0' + miliNum : miliNum,
        });
        // Salvar os valores no localStorage a cada atualização
        salvarNoLocalStorage();
    }, 10);
}

function parar() {
    clearInterval(INTERVALO);
    postMessage({
        action: 'parar',
    });
    // Salvar os valores no localStorage ao parar
    salvarNoLocalStorage();
}

function resetar() {
    clearInterval(INTERVALO);
    miliNum = 0;
    segNum = 0;
    minNum = 0;
    postMessage({
        action: 'resetar',
    });
}

// Função para salvar os valores no localStorage
function salvarNoLocalStorage() {
    const cronometroData = {
        minutos: minNum < 10 ? '0' + minNum : minNum,
        segundos: segNum < 10 ? '0' + segNum : segNum,
        milissegundos: miliNum < 10 ? '0' + miliNum : miliNum,
    };
    localStorage.setItem('cronometroData', JSON.stringify(cronometroData));
}
