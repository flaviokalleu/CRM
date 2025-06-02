const express = require("express");
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, delay } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require("qrcode-terminal");
const fs = require('fs');
const path = require('path');

const app = express();

// Configuration
const config = {
  maxRetries: 3,
  retryDelay: 5000,
  connectionTimeout: 60000,
  messageTimeout: 30000,
  authFolder: './auth_info_baileys'
};

// Global state
let sock = null;
let clientReady = false;
let initializationAttempts = 0;
let lastError = null;
let qrGenerated = false;

// Ensure auth directory exists
if (!fs.existsSync(config.authFolder)) {
  fs.mkdirSync(config.authFolder, { recursive: true });
}

// Initialize client with retry mechanism
const initializeClient = async () => {
  if (initializationAttempts >= config.maxRetries) {
    console.error(`Max initialization attempts (${config.maxRetries}) reached`);
    return false;
  }
  
  initializationAttempts++;
  console.log(`Initialization attempt ${initializationAttempts}/${config.maxRetries}`);
  
  try {
    // Load auth state
    const { state, saveCreds } = await useMultiFileAuthState(config.authFolder);
    
    // Create a proper logger object
    const logger = {
      level: 'silent',
      fatal: () => {},
      error: () => {},
      warn: () => {},
      info: () => {},
      debug: () => {},
      trace: () => {},
      child: () => logger
    };
    
    // Create socket
    sock = makeWASocket({
      auth: state,
      printQRInTerminal: false, // We'll handle QR manually
      logger: logger,
      connectTimeoutMs: config.connectionTimeout,
      defaultQueryTimeoutMs: config.messageTimeout,
      retryRequestDelayMs: 1000,
      maxMsgRetryCount: 3,
      syncFullHistory: false,
      markOnlineOnConnect: true
    });
    
    // Set up event listeners
    setupSocketEvents(saveCreds);
    
    console.log("Client initialized successfully");
    return true;
    
  } catch (error) {
    console.error("Error initializing client:", error.message);
    lastError = error.message;
    
    // Wait before retry
    if (initializationAttempts < config.maxRetries) {
      console.log(`Retrying in ${config.retryDelay / 1000} seconds...`);
      setTimeout(() => {
        initializeClient();
      }, config.retryDelay);
    }
    
    return false;
  }
};

// Setup socket event listeners
const setupSocketEvents = (saveCreds) => {
  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if (qr && !qrGenerated) {
      console.log("QR Code received");
      qrcode.generate(qr, { small: true });
      console.log("Please scan the QR code with your WhatsApp mobile app");
      qrGenerated = true;
    }
    
    if (connection === 'close') {
      const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      
      console.log('Connection closed due to:', lastDisconnect?.error);
      clientReady = false;
      qrGenerated = false;
      
      if (shouldReconnect) {
        console.log('Reconnecting...');
        setTimeout(() => {
          initializationAttempts = 0; // Reset counter for reconnection
          initializeClient();
        }, config.retryDelay);
      } else {
        console.log('Logged out. Please delete auth folder and restart.');
        lastError = 'Logged out - authentication required';
      }
    } else if (connection === 'open') {
      console.log('WhatsApp client is ready!');
      clientReady = true;
      initializationAttempts = 0;
      lastError = null;
      qrGenerated = false;
    }
  });
  
  sock.ev.on('creds.update', saveCreds);
  
  sock.ev.on('messages.upsert', (m) => {
    // Handle incoming messages if needed
    console.log('Received message:', JSON.stringify(m, undefined, 2));
  });
};

// Wait for client to be ready
const waitForClient = (timeout = 30000) => {
  return new Promise((resolve, reject) => {
    if (clientReady && sock) {
      resolve(true);
      return;
    }
    
    const startTime = Date.now();
    const checkInterval = setInterval(() => {
      if (clientReady && sock) {
        clearInterval(checkInterval);
        resolve(true);
      } else if (Date.now() - startTime > timeout) {
        clearInterval(checkInterval);
        reject(new Error('Client not ready within timeout'));
      }
    }, 1000);
  });
};

// Format phone number for WhatsApp
const formatPhoneNumber = (number) => {
  // Remove all non-numeric characters except +
  let cleanNumber = number.replace(/[^\d+]/g, '');
  
  // Remove + if present
  if (cleanNumber.startsWith('+')) {
    cleanNumber = cleanNumber.substring(1);
  }
  
  // Add country code if not present (assuming Brazil +55 if number starts with specific patterns)
  if (cleanNumber.length === 11 && (cleanNumber.startsWith('11') || cleanNumber.startsWith('21') || cleanNumber.startsWith('31'))) {
    cleanNumber = '55' + cleanNumber;
  } else if (cleanNumber.length === 10) {
    cleanNumber = '55' + cleanNumber;
  }
  
  // Return in WhatsApp format
  return cleanNumber + '@s.whatsapp.net';
};

// Send message with retry mechanism
const sendMessageWithRetry = async (number, message, retries = 3) => {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`Sending message attempt ${attempt}/${retries} to ${number}`);
      
      await waitForClient();
      
      // Format number
      const formattedNumber = formatPhoneNumber(number);
      console.log(`Formatted number: ${formattedNumber}`);
      
      // Send message with timeout
      const response = await Promise.race([
        sock.sendMessage(formattedNumber, { text: message }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Message timeout')), config.messageTimeout)
        )
      ]);
      
      console.log(`Message sent successfully: ${response.key.id}`);
      return response;
      
    } catch (error) {
      console.error(`Send attempt ${attempt} failed:`, error.message);
      
      if (attempt === retries) {
        throw error;
      }
      
      // Wait before retry with exponential backoff
      const waitTime = 2000 * Math.pow(2, attempt - 1);
      console.log(`Waiting ${waitTime}ms before retry...`);
      await delay(waitTime);
      
      // Check if we need to reinitialize
      if (!clientReady) {
        console.log("Client not ready, attempting to reinitialize...");
        await initializeClient();
      }
    }
  }
};

// Express middleware
app.use(express.json());

// Send message endpoint
app.post("/send-message", async (req, res) => {
  const { number, message } = req.body;
  
  if (!number || !message) {
    return res.status(400).json({
      success: false,
      error: "Number and message are required"
    });
  }
  
  try {
    const response = await sendMessageWithRetry(number, message);
    
    res.json({
      success: true,
      messageId: response.key.id,
      timestamp: response.messageTimestamp,
      remoteJid: response.key.remoteJid
    });
    
  } catch (error) {
    console.error("Failed to send message:", error.message);
    
    res.status(500).json({
      success: false,
      error: error.message,
      clientReady: clientReady,
      lastError: lastError
    });
  }
});

// Notify correspondent endpoint
app.post("/notify-correspondente", async (req, res) => {
  const { cliente_nome } = req.body;
  
  if (!cliente_nome) {
    return res.status(400).json({
      success: false,
      error: "cliente_nome is required"
    });
  }
  
  try {
    const whatsapp_num = "556196080740"; // Updated to proper format
    const message = `O cliente ${cliente_nome} foi cadastrado com sucesso no sistema.`;
    
    const response = await sendMessageWithRetry(whatsapp_num, message);
    
    res.json({
      success: true,
      messageId: response.key.id,
      timestamp: response.messageTimestamp,
      remoteJid: response.key.remoteJid
    });
    
  } catch (error) {
    console.error("Failed to notify correspondent:", error.message);
    
    res.status(500).json({
      success: false,
      error: error.message,
      clientReady: clientReady,
      lastError: lastError
    });
  }
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "running",
    whatsapp: clientReady ? "ready" : "not_ready",
    attempts: initializationAttempts,
    lastError: lastError,
    timestamp: new Date().toISOString()
  });
});

// Restart endpoint (for debugging)
app.post("/restart", async (req, res) => {
  console.log("Manual restart requested");
  clientReady = false;
  initializationAttempts = 0;
  lastError = null;
  qrGenerated = false;
  
  try {
    if (sock) {
      sock.end();
    }
    await initializeClient();
    res.json({ success: true, message: "Restart initiated" });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Clear auth endpoint (for re-authentication)
app.post("/clear-auth", async (req, res) => {
  try {
    if (sock) {
      sock.logout();
      sock.end();
    }
    
    // Remove auth folder
    if (fs.existsSync(config.authFolder)) {
      fs.rmSync(config.authFolder, { recursive: true, force: true });
    }
    
    clientReady = false;
    initializationAttempts = 0;
    lastError = null;
    qrGenerated = false;
    
    // Recreate auth folder
    fs.mkdirSync(config.authFolder, { recursive: true });
    
    // Reinitialize
    await initializeClient();
    
    res.json({ success: true, message: "Authentication cleared and reinitialized" });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Status endpoint with detailed info
app.get("/status", (req, res) => {
  res.json({
    service: "baileys",
    ready: clientReady,
    attempts: initializationAttempts,
    maxRetries: config.maxRetries,
    lastError: lastError,
    qrGenerated: qrGenerated,
    user: sock?.user || null,
    timestamp: new Date().toISOString()
  });
});

// Get QR endpoint (if needed via API)
app.get("/qr", (req, res) => {
  if (qrGenerated && !clientReady) {
    res.json({ 
      success: true, 
      message: "QR code has been generated. Check console for QR code." 
    });
  } else if (clientReady) {
    res.json({ 
      success: true, 
      message: "Client is already authenticated and ready." 
    });
  } else {
    res.json({ 
      success: false, 
      message: "QR code not available. Try restarting the service." 
    });
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`WhatsApp service (Baileys) running on http://localhost:${PORT}`);
  console.log(`Auth folder: ${config.authFolder}`);
  
  // Initialize client on startup
  initializeClient();
});

// Graceful shutdown
const gracefulShutdown = async (signal) => {
  console.log(`Received ${signal}. Shutting down gracefully...`);
  
  if (sock) {
    try {
      sock.end();
    } catch (error) {
      console.error("Error during client cleanup:", error.message);
    }
  }
  
  process.exit(0);
};

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  gracefulShutdown('uncaughtException');
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});