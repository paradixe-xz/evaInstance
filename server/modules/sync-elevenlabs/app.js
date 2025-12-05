const express = require('express');
const sequelize = require('./config/database');
const conversationRoutes = require('./routes/conversations');
const Conversation = require('./models/Conversation'); // Agregar esta línea
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rutas
app.use('/api/conversations', conversationRoutes);

// Ruta de prueba
app.get('/', (req, res) => {
  res.json({
    message: 'API de ElevenLabs Conversations',
    endpoints: {
      sync: 'POST /api/conversations/sync',
      getAll: 'GET /api/conversations',
      getById: 'GET /api/conversations/:id',
      getAudio: 'GET /api/conversations/:id/audio'
    }
  });
});

// Inicializar base de datos y servidor
async function startServer() {
  try {
    await sequelize.authenticate();
    console.log('Conexión a PostgreSQL establecida correctamente.');
    
    await sequelize.sync({ alter: true });
    console.log('Modelos sincronizados con la base de datos.');
    
    app.listen(PORT, () => {
      console.log(`Servidor ejecutándose en puerto ${PORT}`);
      console.log(`Visita http://localhost:${PORT} para ver los endpoints disponibles`);
    });
  } catch (error) {
    console.error('Error al iniciar el servidor:', error);
  }
}

startServer();

module.exports = app;