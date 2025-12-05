const sequelize = require('../config/database');
const Conversation = require('../models/Conversation');
require('dotenv').config();

async function initDatabase() {
  try {
    await sequelize.authenticate();
    console.log('Conexión a PostgreSQL establecida correctamente.');
    
    // Forzar la creación de las tablas
    await sequelize.sync({ force: true });
    console.log('Base de datos inicializada y tablas creadas.');
    
    console.log('\n=== TABLAS CREADAS ===');
    console.log('✅ conversations');
    
    process.exit(0);
  } catch (error) {
    console.error('Error inicializando la base de datos:', error);
    process.exit(1);
  }
}

initDatabase();