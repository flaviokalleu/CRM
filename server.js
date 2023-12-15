const express = require("express");
const { Client } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");

const app = express();
const client = new Client();

client.on("qr", (qr) => {
  // Exibe o QR Code no terminal
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  console.log("Cliente está pronto!");
});

client.initialize();

app.use(express.json());

app.post("/send-message", (req, res) => {
  const number = req.body.number;
  const message = req.body.message;

  client
    .sendMessage(number, message)
    .then((response) => {
      return res.json({ success: true });
    })
    .catch((err) => {
      return res.json({ success: false, error: err.message });
    });
});

// Endpoint adicionado
app.post("/notify-correspondente", (req, res) => {
  const cliente_nome = req.body.cliente_nome;

  // Dummy data para o exemplo. Na vida real, você provavelmente consultaria o banco de dados aqui.
  const whatsapp_num = "556196551446@c.us";

  const message = `O cliente *${cliente_nome}* foi cadastrado com sucesso no sistema.`;

  client
    .sendMessage(whatsapp_num, message)
    .then((response) => {
      return res.json({ success: true });
    })
    .catch((err) => {
      return res.json({ success: false, error: err.message });
    });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
